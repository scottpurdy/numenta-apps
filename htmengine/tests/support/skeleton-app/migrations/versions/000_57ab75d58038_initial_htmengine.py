# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Initial htmengine

Revision ID: 57ab75d58038
Revises: None
Create Date: 2014-12-09 10:51:09.476572
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# Revision identifiers, used by Alembic. Do not change.
revision = '57ab75d58038'
down_revision = None



def upgrade():
  """ Initial Taurus table schema generated by `alembic revision --autogenerate`
  """
  # Schema: instance_status_history
  op.create_table('instance_status_history',
    sa.Column('server', sa.VARCHAR(length=100), server_default='',
              nullable=False),
    sa.Column('timestamp', sa.TIMESTAMP(), server_default='0000-00-00 00:00:00',
              nullable=False),
    sa.Column('status', sa.VARCHAR(length=32), server_default='',
              nullable=False),
    sa.PrimaryKeyConstraint('server', 'timestamp')
  )

  # Schema: lock
  op.create_table('lock',
    sa.Column('name', sa.VARCHAR(length=40), nullable=False),
    sa.PrimaryKeyConstraint('name')
  )
  op.execute("INSERT INTO `lock` (`name`) VALUES('metrics')")

  # Schema: metric
  op.create_table('metric',
    sa.Column('uid', sa.VARCHAR(length=40), nullable=False),
    sa.Column('datasource', sa.VARCHAR(length=100), nullable=True),
    sa.Column('name', sa.VARCHAR(length=255), nullable=True),
    sa.Column('description', sa.VARCHAR(length=200), nullable=True),
    sa.Column('server', sa.VARCHAR(length=100), nullable=True),
    sa.Column('location', sa.VARCHAR(length=200), nullable=True),
    sa.Column('parameters', sa.TEXT(), nullable=True),
    sa.Column('status', sa.INTEGER(), server_default='0', autoincrement=False,
              nullable=True),
    sa.Column('message', sa.TEXT(), nullable=True),
    sa.Column('collector_error', sa.TEXT(), nullable=True),
    sa.Column('last_timestamp', sa.TIMESTAMP(), nullable=True),
    sa.Column('poll_interval', sa.INTEGER(), server_default='60',
              autoincrement=False, nullable=True),
    sa.Column('tag_name', sa.VARCHAR(length=200), nullable=True),
    sa.Column('model_params', sa.TEXT(), nullable=True),
    sa.Column('last_rowid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uid')
  )
  op.create_index('datasource_idx', 'metric', ['datasource'], unique=False)
  op.create_index('location_idx', 'metric', ['location'], unique=False)
  op.create_index('server_idx', 'metric', ['server'], unique=False)

  # Schema: metric_data
  op.create_table('metric_data',
    sa.Column('uid', sa.VARCHAR(length=40), server_default='', nullable=False),
    sa.Column('rowid', sa.INTEGER(), server_default='0', autoincrement=False,
              nullable=False),
    sa.Column('timestamp', sa.TIMESTAMP(),
              server_default=sa.func.current_timestamp(), nullable=False),
    sa.Column('metric_value', mysql.DOUBLE(), nullable=False),
    sa.Column('raw_anomaly_score', mysql.DOUBLE(), nullable=True),
    sa.Column('anomaly_score', mysql.DOUBLE(), nullable=True),
    sa.Column('display_value', sa.INTEGER(), autoincrement=False,
              nullable=True),
    sa.ForeignKeyConstraint(['uid'], [u'metric.uid'],
      name='metric_data_to_metric_fk', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('uid', 'rowid')
  )
  op.create_index('anomaly_score_idx', 'metric_data', ['anomaly_score'],
                  unique=False)
  op.create_index('timestamp_idx', 'metric_data', ['timestamp'], unique=False)
  ### end Alembic commands ###



def downgrade():
  raise NotImplementedError("Rollback is not supported.")
