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

"""Impelementation of the distutils command extension for resetting Taurus
Engine's message queues/exchanges, model checkpoints, and repository database.
NOTE: must be executed while all Taurus Engine and Taurus Collector services are
stopped.
"""

import argparse
import logging
import random
import sys
import traceback

from nta.utils import amqp
from nta.utils.error_handling import logExceptions
from nta.utils.message_bus_connector import MessageBusConnector
from nta.utils import prompt_utils

from htmengine.model_checkpoint_mgr import model_checkpoint_mgr
from htmengine import model_swapper

import taurus.engine
from taurus.engine import logging_support
import taurus.engine.repository
from taurus.engine.runtime.dynamodb.dynamodb_service import DynamoDBService



_WARNING_PROMPT_TIMEOUT_SEC = 30



class UserAbortedOperation(Exception):
  """When prompted with a warning about this destructive action, the user
  aborted this operation.
  """
  pass



g_log = logging.getLogger(__name__)



def _parseArgs(args):
  """Parse command-line arguments

  :param list args: The equivalent of `sys.argv[1:]`

  :returns: the args object generated by ``argparse.ArgumentParser.parse_args``
    with the following attributes:
      suppressPrompt: True to suppress destructive action warning prompt
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "--suppress-prompt-and-obliterate",
    action="store_true",
    dest="suppressPrompt",
    help=("Suppress confirmation prompt and proceed with this DESTRUCTIVE "
          "operation. This option is intended for scripting."))

  return parser.parse_args(args)



def _warnAboutDestructiveAction():
  """Warn user about destructive action.

  :raises nta.utils.prompt_utils.PromptTimeout: if prompt timed out
  :raises UserAbortedOperation: if user chose to abort the operation
  """
  expectedAnswer = "Yes-{randomNum}".format(randomNum=random.randint(1, 30),)

  promptText = (
    "\n"
    "ATTENTION!  You are about to reset Taurus Engine's message "
    "queues/exchanges, model checkpoints, and repository.\n"
    "\n"
    "To back out immediately without making any changes, feel free to type "
    "anything but \"{expectedAnswer}\" in the prompt below, and press "
    "return. (auto-abort in {timeout} seconds)\n"
    "\n"
    "Are you sure you want to continue? "
    .format(expectedAnswer=expectedAnswer, timeout=_WARNING_PROMPT_TIMEOUT_SEC))

  answer = prompt_utils.promptWithTimeout(
    promptText=promptText,
    timeout=_WARNING_PROMPT_TIMEOUT_SEC)


  if answer != expectedAnswer:
    raise UserAbortedOperation(
      "User aborted operation from warning prompt; "
      "expectedAnswer={expectedAnswer}, but got actual={actual}".format(
        expectedAnswer=expectedAnswer, actual=answer))



def _cleanRabbitmq():
  """Delete Taurus Engine-related message queues and exchanges"""
  g_log.info("Deleting Taurus Engine-related message queues and exchanges")

  appConfig = taurus.engine.config

  modelSwapperConfig = model_swapper.ModelSwapperConfig()

  # Delete queues belonging to Taurus
  taurusQueues = [
    modelSwapperConfig.get("interface_bus", "results_queue"),
    modelSwapperConfig.get("interface_bus", "scheduler_notification_queue"),

    appConfig.get("metric_listener", "queue_name"),

    DynamoDBService._INPUT_QUEUE_NAME  # pylint: disable=W0212
  ]

  modelInputPrefix = modelSwapperConfig.get("interface_bus",
                                            "model_input_queue_prefix")

  with MessageBusConnector() as messageBus:
    for queue in messageBus.getAllMessageQueues():
      if queue.startswith(modelInputPrefix) or queue in taurusQueues:
        messageBus.deleteMessageQueue(queue)


  # Delete exchanges belonging to Taurus
  taurusExchanges = [
    appConfig.get("metric_streamer", "results_exchange_name"),
    appConfig.get("non_metric_data", "exchange_name")
  ]

  amqpClient = amqp.synchronous_amqp_client.SynchronousAmqpClient(
    connectionParams=amqp.connection.getRabbitmqConnectionParameters())

  with amqpClient:
    for exg in taurusExchanges:
      g_log.info("Deleting Taurus exchange=%s", exg)
      amqpClient.deleteExchange(exchange=exg)



def _cleanRepository():
  """Reset Taurus Engine's repository database"""
  g_log.info("Resetting repository")

  taurus.engine.repository.reset(suppressPromptAndContinueWithDeletion=True)



def _cleanModelCheckpoints():
  """Delete all model checkpoints"""
  g_log.info("Deleting model checkpoints")

  model_checkpoint_mgr.ModelCheckpointMgr.removeAll()



def _resetAll(suppressPrompt):
  """Reset Taurus Engine's message queues/exchanges, model checkpoints, and
  repository database. NOTE: must be executed while all Taurus Engine and Taurus
  Collector services are stopped.

  :param bool suppressPrompt: True to suppress confirmation prompt and proceed
    with this DESTRUCTIVE operation. This option is intended for scripting.
  """
  g_log.warning("Invoked with suppressPrompt=%s; traceback=%s",
                suppressPrompt, traceback.format_stack())

  if not suppressPrompt:
    _warnAboutDestructiveAction()

  # Delete Taurus Engine-related message queues and exchanges
  _cleanRabbitmq()


  # Reset Taurus Engine's repository database
  _cleanRepository()


  # Delete model checkpoints
  _cleanModelCheckpoints()



@logExceptions(g_log)
def main(args):
  """
  :param list args: The equivalent of `sys.argv[1:]`
  """

  try:
    args = _parseArgs(args)
  except SystemExit as exc:
    if exc.code == 0:
      # Suppress exception logging when exiting due to --help
      return

    raise


  _resetAll(suppressPrompt=args.suppressPrompt)



if __name__ == "__main__":
  logging_support.LoggingSupport.initTool()

  main(sys.argv[1:])
