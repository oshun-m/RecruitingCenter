# interviews/blueprints/interviews.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from decorators.auth import login_required
from decorators.access import group_required
from model_route import run_sql

from interviews.services.candidates import get_candidates_by_vacancy
from interviews_model import appointment_menu_context, appointment_candidates_context, appointment_add_candidate, appointment_remove_candidate, appointment_confirm

bp = Blueprint('interviews', __name__, template_folder='../templates')


@bp.route('/menu')
@login_required
@group_required()
def menu():
    ctx = appointment_menu_context()
    return render_template(
        'interview_menu.html',
        vacancies=ctx["vacancies"],
        employees=ctx["employees"],
    )


@bp.get('/candidates')
@login_required
@group_required()
def candidates():
    vac_id = int(request.args['vac_id'])
    date = request.args['date']
    emp_id = request.args.get('emp_id', type=int)

    ctx = appointment_candidates_context(vac_id, date, emp_id)
    if ctx["error"] == "vacancy_closed":
        flash('Вакансия закрыта или недоступна', 'danger')
        return redirect(url_for('interviews.menu'))

    return render_template(
        'interview_candidates.html',
        vac_id=ctx["vac_id"],
        date=ctx["date"],
        emp_id=ctx["emp_id"],
        candidates=ctx["candidates"],
        basket=ctx["basket"],
    )


@bp.post('/add_ajax')
@login_required
@group_required()
def add_ajax():
    data = request.get_json()
    vac_id = int(data['vac_id'])
    date = data['date']
    emp_id = data.get('emp_id')
    cand_id = int(data['cand_id'])

    basket = appointment_add_candidate(vac_id, date, emp_id, cand_id)
    return render_template('basket_block.html', basket=basket)


@bp.post('/remove_ajax')
@login_required
@group_required()
def remove_ajax():
    data = request.get_json()
    vac_id = int(data['vac_id'])
    date = data['date']
    emp_id = data.get('emp_id')
    cand_id = int(data['cand_id'])

    basket = appointment_remove_candidate(vac_id, date, emp_id, cand_id)
    return render_template('basket_block.html', basket=basket)

@bp.post('/confirm')
@login_required
@group_required()
def confirm():
    vac_id = int(request.form['vac_id'])
    date = request.form['date']
    emp_id = int(request.form['emp_id'])

    result = appointment_confirm(vac_id, date, emp_id)

    if result["error"] == "basket_empty":
        flash('Корзина пуста. Выберите хотя бы одного кандидата.', 'warning')
        return redirect(url_for('interviews.candidates', vac_id=vac_id, date=date, emp_id=emp_id))

    flash(f'Создано приглашений: {result["created"]}', 'success')
    return redirect(url_for('interviews.menu'))
