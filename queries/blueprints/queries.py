from flask import Blueprint, render_template, request, flash, redirect, url_for
from functools import wraps
from decorators.auth import login_required
from decorators.access import group_required
from model_route import run_sql, ModelRouteError

bp = Blueprint('queries', __name__, template_folder='../templates')



QUERIES = {
    "new_employees": {
        "title": "Новые сотрудники за период",
        "sql": "new_emp.sql",
        "fields": [
            {"name": "start_date", "label": "Начальная дата", "type": "date", "required": True},
            {"name": "end_date",   "label": "Конечная дата",  "type": "date", "required": True},
            {"name": "office_id",  "label": "Номер офиса",    "type": "int",  "required": False},
        ],
    },
    "last_open_vacancy": {
        "title": "Дата последней открытой вакансии",
        "sql": "last_open_vacancy.sql",
        "fields": [
            {"name": "job_id",     "label": "Код должности", "type": "int",  "required": False},
            {"name": "office_id",  "label": "Номер офиса",   "type": "int",  "required": False},
        ],
    },
    "open_vacancies_by_month": {
        "title": "Открытые вакансии по месяцам выбранного года",
        "sql": "open_vacancies.sql",
        "fields": [
            {"name": "year",       "label": "Год",           "type": "int",  "required": True},
            {"name": "office_id",  "label": "Номер офиса",   "type": "int",  "required": False},
            {"name": "job_id",     "label": "Код должности", "type": "int",  "required": False},
        ],
    },
}


def _coerce(value: str, ftype: str):
    if value is None or value == "":
        return None
    if ftype in ("int", "number"):
        return int(value)
    return value  # date/text

@bp.errorhandler(ModelRouteError)
def handle_model_error(e: ModelRouteError):
    flash(str(e), "error")
    qid = request.form.get('qid') or request.args.get('qid')
    meta = QUERIES.get(qid) if qid else None
    return render_template(
        'query_form.html',
        qid=qid,
        queries=QUERIES,
        title=(meta["title"] if meta else "Параметризованный запрос"),
        fields=(meta["fields"] if meta else []),
        params=request.form
    ), 400


@bp.route('/run', defaults={'qid': None}, methods=['GET'])
@bp.route('/run/<qid>', methods=['GET'])
@login_required
@group_required()
def query_form_root(qid):
    qid = qid or request.args.get('qid')
    meta = QUERIES.get(qid) if qid else None
    return render_template(
        'query_form.html',
        qid=qid,
        queries=QUERIES,
        title=(meta["title"] if meta else "Параметризованный запрос"),
        fields=(meta["fields"] if meta else []),
        params={}
    )


@bp.route('/run', methods=['POST'])
@login_required
@group_required()
def query_run():
    qid = request.form.get('qid')
    meta = QUERIES.get(qid)
    if not meta:
        flash("Выберите запрос", "error")
        return redirect(url_for('queries.query_form_root'))

    params = {}
    for f in meta["fields"]:
        raw = (request.form.get(f["name"]) or "").strip()
        try:
            params[f["name"]] = _coerce(raw, f["type"])
        except ValueError:
            flash(f"Поле «{f['label']}» задано неверно", "error")
            return render_template(
                'query_form.html',
                title=meta["title"], qid=qid,
                queries=QUERIES,
                fields=meta["fields"],
                params=request.form
            )

    rows = run_sql(meta["sql"], params)
    headers = list(rows[0].keys()) if rows else []

    labels = {f["name"]: f["label"] for f in meta["fields"]}
    filters_display = [(labels[name], params.get(name)) for name in labels.keys()]

    return render_template(
        'query_result.html',
        title=meta["title"], qid=qid,
        headers=headers, rows=rows,
        filters_display=filters_display
    )
