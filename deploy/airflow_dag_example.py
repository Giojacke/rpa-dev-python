"""Example: minimal Airflow DAG that runs the bot.

One Airflow task = one full run of the bot (main.py). The RPA tasks inside
the bot (LoginTask, ...) are NOT Airflow tasks; their order and retries are
handled by process.py and core/base_task.py.

Secrets come from Airflow, not from code:
- Connection `rpa_sample_login` (login/password) -> RPA_USERNAME / RPA_PASSWORD
- Variable `rpa_sample_login_base_url`            -> RPA_BASE_URL

Written for Airflow 2.x. On Airflow 3 import BashOperator from
`airflow.providers.standard.operators.bash`.
"""

from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

BOT_DIR = "/opt/rpa/rpa-sample-login"

with DAG(
    dag_id="rpa_sample_login",
    schedule="0 6 * * 1-5",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["rpa"],
) as dag:
    run_bot = BashOperator(
        task_id="run_bot",
        bash_command=f"cd {BOT_DIR} && python main.py",
        append_env=True,
        env={
            "RPA_PROCESS_NAME": "sample_login",
            "RPA_ENGINE": "playwright",
            "RPA_HEADLESS": "true",
            "RPA_BASE_URL": "{{ var.value.rpa_sample_login_base_url }}",
            "RPA_USERNAME": "{{ conn.rpa_sample_login.login }}",
            "RPA_PASSWORD": "{{ conn.rpa_sample_login.password }}",
        },
        # The bot already retries each RPA task internally (RPA_MAX_RETRIES).
        # Keep Airflow retries at 0 to avoid re-running the whole process.
        retries=0,
    )
