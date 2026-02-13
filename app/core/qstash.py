# app/core/qstash.py
import os
from qstash import Receiver


receiver = Receiver(
    current_signing_key=os.environ["QSTASH_CURRENT_SIGNING_KEY"],
    next_signing_key=os.environ.get("QSTASH_NEXT_SIGNING_KEY"),
)
