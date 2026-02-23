from typing import Dict, Any, List
from flask import session
from model_route import run_sql, run_sql_one, exec_sql
from interviews.services.candidates import get_candidate_by_id


def _basket_store() -> Dict[str, Any]:

    store = session.get('interview_baskets')
    if store is None or not isinstance(store, dict):
        store = {}
        session['interview_baskets'] = store
    return store


def _basket_key(vac_id: int, date_str: str) -> str:
    return f"{int(vac_id)}|{date_str}"


def load_basket(vac_id: int, date_str: str) -> Dict[str, Any]:
    """
    Получить корзину для (vac_id, date) из сессии.
    Если её ещё нет — создать пустую.
    """
    store = _basket_store()
    key = _basket_key(vac_id, date_str)

    basket = store.get(key)
    if not isinstance(basket, dict):
        basket = {
            "vac_id": int(vac_id),
            "date": date_str,
            "emp_id": None,
            "items": {}
        }
        store[key] = basket
        session.modified = True

    basket.setdefault("vac_id", int(vac_id))
    basket.setdefault("date", date_str)
    basket.setdefault("emp_id", None)
    basket.setdefault("items", {})

    return basket


def save_basket(vac_id: int, date_str: str, basket: Dict[str, Any]) -> None:
    """Сохранить корзину в сессию."""
    store = _basket_store()
    key = _basket_key(vac_id, date_str)
    store[key] = basket
    session.modified = True


def clear_basket(vac_id: int, date_str: str) -> None:
    """Удалить корзину для (vac_id, date) из сессии."""
    store = _basket_store()
    key = _basket_key(vac_id, date_str)
    if key in store:
        del store[key]
        session.modified = True


def set_emp(vac_id: int, date_str: str, emp_id: int | None) -> Dict[str, Any]:
    """Зафиксировать интервьюера для корзины."""
    basket = load_basket(vac_id, date_str)
    basket["emp_id"] = int(emp_id) if emp_id is not None else None
    save_basket(vac_id, date_str, basket)
    return basket


def add_candidate(vac_id: int, date_str: str, cand_id: int) -> Dict[str, Any]:
    """
    Возвращает обновлённую корзину.
    """
    basket = load_basket(vac_id, date_str)
    items = basket.setdefault("items", {})

    cand = get_candidate_by_id(cand_id)
    if not cand:
        return basket

    snapshot = {
        "cand_id": int(cand["cand_id"]),
        "full_name": cand.get("full_name"),
        "age": cand.get("age"),
        "gender": cand.get("gender"),
        "job_id": cand.get("job_id"),
        "vac_id": int(vac_id),
        "status": "planned",
    }

    items[str(snapshot["cand_id"])] = snapshot
    save_basket(vac_id, date_str, basket)
    return basket


def remove_candidate(vac_id: int, date_str: str, cand_id: int) -> Dict[str, Any]:
    """Удалить кандидата из корзины по id. Возвращает обновлённую корзину."""
    basket = load_basket(vac_id, date_str)
    items = basket.setdefault("items", {})
    items.pop(str(int(cand_id)), None)
    save_basket(vac_id, date_str, basket)
    return basket



def vacancy_is_open(vac_id: int) -> bool:
    """Проверить, открыта ли вакансия. SQL: vacancy_is_open.sql"""
    return bool(run_sql_one('vacancy_is_open.sql', {"vac_id": vac_id}))


def find_event_by_vac_date(vac_id: int, date: str):
    """Найти событие interview по вакансии и дате. SQL: interview_event_by_vac_date.sql"""
    return run_sql_one('interview_event_by_vac_date.sql', {
        "vac_id": vac_id,
        "date": date
    })


def ensure_event(vac_id: int, date: str, emp_id: int):
    """
    Гарантировать наличие события interview для (vac_id, date).
    - если события нет → INSERT в interview и повторный SELECT;
    - если есть и emp_id не установлен → UPDATE interview.emp_id;
    - иначе вернуть существующее событие.
    """
    evt = find_event_by_vac_date(vac_id, date)
    if not evt:
        exec_sql('interview_event_insert.sql', {
            "vac_id": vac_id,
            "date": date,
            "emp_id": emp_id
        })
        return find_event_by_vac_date(vac_id, date)

    if not evt.get('emp_id') and emp_id:
        exec_sql('interview_event_update_emp.sql', {
            "event_id": evt['event_id'],
            "emp_id": emp_id
        })
        evt['emp_id'] = emp_id

    return evt


def call_exists(event_id: int, cand_id: int) -> bool:
    """Проверить, есть ли уже приглашение для кандидата на это событие."""
    return bool(run_sql_one('calls_exists.sql', {
        "event_id": event_id,
        "cand_id": cand_id
    }))


def create_calls_for_event(event_id: int, emp_id: int, cand_ids: List[int]) -> int:
    created = 0
    for cid in cand_ids:
        cid = int(cid)
        if not call_exists(event_id, cid):
            exec_sql('interview_call_insert.sql', {
                "event_id": event_id,
                "emp_id": emp_id,
                "cand_id": cid,
                "status": None
            })
            created += 1
    return created



def appointment_menu_context() -> Dict[str, Any]:
    """
    Данные для страницы выбора вакансии / даты / интервьюера.
    """
    vacancies = run_sql('interview_vacancies_open.sql', {})
    employees = run_sql('interview_employees.sql', {})

    return {
        "vacancies": vacancies,
        "employees": employees,
    }


def appointment_candidates_context(vac_id: int, date: str, emp_id: int | None) -> Dict[str, Any]:
    if not vacancy_is_open(vac_id):
        return {"error": "vacancy_closed"}

    set_emp(vac_id, date, emp_id)

    from interviews.services.candidates import get_candidates_by_vacancy
    candidates = get_candidates_by_vacancy(vac_id)

    basket = load_basket(vac_id, date)

    return {
        "vac_id": vac_id,
        "date": date,
        "emp_id": emp_id,
        "candidates": candidates,
        "basket": basket,
        "error": None,
    }


def appointment_add_candidate(vac_id: int, date: str, emp_id: int | None, cand_id: int) -> Dict[str, Any]:
    """Добавить кандидата в корзину и вернуть обновлённую корзину."""
    set_emp(vac_id, date, emp_id)
    basket = add_candidate(vac_id, date, cand_id)
    return basket


def appointment_remove_candidate(vac_id: int, date: str, emp_id: int | None, cand_id: int) -> Dict[str, Any]:
    """Удалить кандидата из корзины и вернуть обновлённую корзину."""
    set_emp(vac_id, date, emp_id)
    basket = remove_candidate(vac_id, date, cand_id)
    return basket


def appointment_confirm(vac_id: int, date: str, emp_id: int) -> Dict[str, Any]:
    basket = load_basket(vac_id, date)
    items = basket.get("items") or {}

    if not items:
        return {"created": 0, "error": "basket_empty"}

    evt = ensure_event(vac_id, date, emp_id)
    cand_ids: List[int] = [int(cid) for cid in items.keys()]
    created = create_calls_for_event(evt['event_id'], evt['emp_id'], cand_ids)

    clear_basket(vac_id, date)

    return {"created": created, "error": None}
