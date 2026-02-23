
from flask import current_app
from decorators.redis import fetch_from_cache
from model_route import run_sql, run_sql_one


def _cache_cfg():
    return current_app.config['CACHE_CONFIG']


@fetch_from_cache("cand_by_vac:{vac_id}", _cache_cfg)
def get_candidates_by_vacancy(vac_id: int):
    return run_sql('interview_candidates_by_vacancy.sql', {"vac_id": vac_id})


@fetch_from_cache("cand_by_id:{cand_id}", _cache_cfg)
def get_candidate_by_id(cand_id: int):
    return run_sql_one('interview_candidate_by_id.sql', {"cand_id": cand_id})
