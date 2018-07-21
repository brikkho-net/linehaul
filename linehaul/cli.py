# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import importlib_resources
import json

from functools import partial

import asks
import click
import trio

from linehaul.bigquery import BigQuery
from linehaul.migration import migrate as migrate_
from linehaul.server import server as server_


asks.init("trio")


@click.group(context_settings={"auto_envvar_prefix": "LINEHAUL"})
def cli():
    pass


@cli.command()
@click.option("--bind", default="0.0.0.0")
@click.option("--port", type=int, default=512)
@click.option("--token")
@click.option("--credentials", type=click.File("r", encoding="utf8"), required=True)
@click.option("--batch-size", type=int, default=3)  # TODO: Change to 500
@click.option("--batch-timeout", type=int, default=30)
@click.option("--queued-events", type=int, default=10000)
@click.argument("table")
def server(
    bind, port, token, credentials, batch_size, batch_timeout, queued_events, table
):
    credentials = json.load(credentials)
    bq = BigQuery(credentials["client_email"], credentials["private_key"])

    trio.run(
        partial(
            server_,
            bq,
            table,
            bind=bind,
            port=port,
            token=token,
            qsize=queued_events,
            batch_size=batch_size,
            batch_timeout=batch_timeout,
        ),
        restrict_keyboard_interrupt_to_checkpoints=True,
    )


@cli.command()
@click.option("--credentials", type=click.File("r", encoding="utf8"), required=True)
@click.argument("table")
def migrate(credentials, table):
    credentials = json.load(credentials)
    bq = BigQuery(credentials["client_email"], credentials["private_key"])
    schema = json.loads(importlib_resources.read_text("linehaul", "schema.json"))

    trio.run(migrate_, bq, table, schema)
