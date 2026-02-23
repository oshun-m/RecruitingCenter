from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from decorators.access import group_required
from model_route import run_sql, run_sql_one, call_proc, ModelRouteError
import json

bp = Blueprint('reports', __name__, template_folder='../templates')

REPORTS = {
    "interviews_monthly": {
        "title":      "Собеседования по рекрутерам за месяц (по открытым вакансиям)",
        "build_proc": "p_interviews_monthly",
        "exists_sql": "interviews_monthly_exists.sql",
        "select_sql": "interviews_monthly_select.sql",
        "arg_order":  ["p_month", "p_year", "p_office_id"],
        "fields": [
            {"name": "p_month",     "label": "Месяц (1–12)", "type": "int", "required": True},
            {"name": "p_year",      "label": "Год",          "type": "int", "required": True},
            {"name": "p_office_id", "label": "Номер офиса",  "type": "int", "required": False},
        ],
    },
    "monthly_proc_recruiting": {
        "title":      "Месячный отчёт по найму",
        "build_proc": "p_recruiting_report",
        "exists_sql": "recruiting_monthly_exists.sql",
        "select_sql": "recruiting_monthly_select.sql",
        "arg_order":  ["p_month", "p_year", "p_office_id"],
        "fields": [
            {"name": "p_month",     "label": "Месяц (1–12)", "type": "int", "required": True},
            {"name": "p_year",      "label": "Год",          "type": "int", "required": True},
            {"name": "p_office_id", "label": "Номер офиса",  "type": "int", "required": False},
        ],
    },
}

def _has_access(code: str) -> bool:
    """Проверка права в конфиге приложения"""
    role = session.get('user_group') or (session.get('user') or {}).get('role')
    access = (current_app.config.get('db_access') or {})
    allowed = set(access.get(role, []))
    return role == 'admin' or '*' in allowed or code in allowed

def _call_proc_smart(proc_name, args_try_first):
    try:
        return call_proc(proc_name, args_try_first)
    except ModelRouteError as e:
        code = getattr(e, 'code', None)
        if (code == 1318) or ('1318' in str(e)):
            current_user = (session.get('user') or {}).get('login')
            return call_proc(proc_name, args_try_first + [current_user])
        raise

def _collect_monthly_params(meta, form):
    """Сбор и валидация полей формы (месяц/год/офис). Возвращает (params, errors)"""
    params, errors = {}, []
    for field in meta.get('fields', []):
        name = field['name']
        label = field['label']
        ftype = field.get('type', 'str')
        required = field.get('required', False)

        raw_value = (form.get(name, '') or '').strip()
        if raw_value == '':
            if required:
                errors.append(f"Поле «{label}» обязательно для заполнения")
            params[name] = None
            continue

        if ftype == 'int':
            try:
                params[name] = int(raw_value)
            except ValueError:
                errors.append(f"Поле «{label}» должно быть целым числом")
                params[name] = None
        else:
            params[name] = raw_value
    return params, errors

def _exists_ready(meta, params):
    """Проверка: есть ли готовые строки в агрегатной таблице за месяц/год/офис"""
    try:
        ex = run_sql_one(meta['exists_sql'], {
            "p_month": params.get("p_month"),
            "p_year": params.get("p_year"),
            "p_office_id": params.get("p_office_id"),
        }, required=True) or {}
    except ModelRouteError as e:
        raise e
    return (ex.get('cnt') or ex.get('count') or 0) > 0

def _select_ready(meta, params):
    """Чтение готовых строк из агрегатной таблицы"""
    return run_sql(meta['select_sql'], {
        "p_month": params.get("p_month"),
        "p_year": params.get("p_year"),
        "p_office_id": params.get("p_office_id"),
    }) or []

@bp.route('/run', defaults={'rid': None}, methods=['GET'])
@bp.route('/run/<rid>', methods=['GET'])
@group_required()
def report_form_root(rid):
    if rid is None:
        return render_template(
            'reports_form.html',
            reports=REPORTS,
            selected_id=None,
            rid=None,
            meta=None,
            params={}
        )
    if rid not in REPORTS:
        flash('Неизвестный отчёт', 'error')
        return redirect(url_for('reports.report_form_root'))

    meta = REPORTS[rid]
    return render_template(
        'reports_form.html',
        reports=REPORTS,
        selected_id=rid,
        rid=rid,
        meta=meta,
        report_id=rid,
        params={}
    )

# ==== POST: Создать / Смотреть готовые ====
@bp.route('/run', methods=['POST'])
@group_required()
def report_run():
    rid = request.form.get('report_id')
    action = request.form.get('action')
    if not rid or rid not in REPORTS or action not in ('create', 'view'):
        flash('Некорректный запрос', 'error')
        return redirect(url_for('reports.report_form_root'))

    meta = REPORTS[rid]
    params, errors = _collect_monthly_params(meta, request.form)

    if errors:
        for e in errors: flash(e, 'error')
        return render_template(
            'reports_form.html',
            reports=REPORTS, selected_id=rid, rid=rid, meta=meta, report_id=rid, params=params
        )
    if action == 'view':
        try:
            ready = _exists_ready(meta, params)
        except ModelRouteError as e:
            flash(f'Ошибка проверки наличия отчёта: {e}', 'error')
            ready = False

        if not ready:
            flash('Такого отчёта за указанный месяц нет.', 'error')
            return render_template(
                'reports_form.html',
                reports=REPORTS, selected_id=rid, rid=rid, meta=meta, report_id=rid, params=params
            )

        try:
            rows = _select_ready(meta, params)
        except ModelRouteError as e:
            flash(f'Ошибка чтения отчёта: {e}', 'error')
            rows = []

        return render_template('reports_result.html', meta=meta, rows=rows, report_id=rid)

    # ==== Создать отчёт ====
    if not _has_access('reports_build'):
        flash('Нет права на создание отчётов', 'error')
        return redirect(url_for('reports.report_form_root', rid=rid))

    try:
        if _exists_ready(meta, params):
            flash('Отчёт за этот месяц уже существует — показываю готовый.', 'success')
            rows = _select_ready(meta, params)
            return render_template('reports_result.html', meta=meta, rows=rows, report_id=rid)
    except ModelRouteError as e:
        flash(f'Ошибка проверки наличия отчёта: {e}', 'error')
        return render_template(
            'reports_form.html',
            reports=REPORTS, selected_id=rid, rid=rid, meta=meta, report_id=rid, params=params
        )

    try:
        args = [params.get("p_month"), params.get("p_year"), params.get("p_office_id")]
        rows = _call_proc_smart(meta['build_proc'], args)
    except ModelRouteError as e:
        flash(f'Ошибка при создании отчёта: {e}', 'error')
        return render_template(
            'reports_form.html',
            reports=REPORTS, selected_id=rid, rid=rid, meta=meta, report_id=rid, params=params
        )

    try:
        rows = _select_ready(meta, params)
    except ModelRouteError as e:
        flash(f'Ошибка чтения отчёта после создания: {e}', 'error')
        rows = rows or []

    # логирование в историю
    try:
        payload = json.dumps(params, ensure_ascii=False)
        current_user = (session.get('user') or {}).get('login')
        run_sql('report_log_insert.sql', {
            "report_id": rid,
            "params_json": payload,
            "row_count": len(rows) if rows else 0,
            "created_by": current_user,
        })

    except ModelRouteError as e:
        flash(f'Не удалось записать отчёт в историю: {e}', 'error')

    flash('Отчёт создан.', 'success')
    return render_template('reports_result.html', meta=meta, rows=rows, report_id=rid)

# ==== Просмотр из истории ====
@bp.route('/history', methods=['GET'])
@group_required()
def report_history():
    try:
        rows = run_sql('report_log_list.sql', {})
    except ModelRouteError as e:
        flash(f'Ошибка при получении истории отчётов: {e}', 'error')
        rows = []
    return render_template('reports_history.html', logs=rows, rows=rows, reports=REPORTS)

@bp.route('/view/<int:log_id>', methods=['GET'])
@group_required()
def report_view(log_id: int):
    try:
        log_row = run_sql_one('report_log_get.sql', {"log_id": log_id}, required=True)
    except ModelRouteError as e:
        flash(f'Отчёт не найден: {e}', 'error')
        return redirect(url_for('reports.report_history'))

    rid = log_row.get('report_id')
    params_json = log_row.get('params_json') or '{}'
    try:
        params = json.loads(params_json)
    except ValueError:
        params = {}

    meta = REPORTS.get(rid)
    if not meta:
        flash('Тип отчёта больше не существует в системе', 'error')
        return redirect(url_for('reports.report_history'))

    try:
        rows = _select_ready(meta, params)
    except ModelRouteError as e:
        flash(f'Ошибка при чтении отчёта: {e}', 'error')
        rows = []

    return render_template('reports_result.html', meta=meta, rows=rows, log_id=log_id, report_id=rid)
