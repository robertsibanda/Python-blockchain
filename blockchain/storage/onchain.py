"""On-chain data persistence — stores verified transaction data into MongoDB collections."""
import sys
from typing import Any

from blockchain.block import Block
from blockchain.blockchain import Chain
from blockchain.security import create_hash_default
from blockchain.storage import database
from blockchain.transaction import Transaction


def get_patient_records(db, patient):
    """Placeholder: retrieve patient records from database."""
    return


def save_transaction(db: database.Database, transaction: Transaction) -> None:
    """Persist transaction data to the appropriate MongoDB collection based on type.

    Args:
        db: Database instance.
        transaction: The transaction to persist.
    """
    data = dict(transaction.data)

    if transaction.type_ == "record":
        patient = transaction.metadata['patient']
        db.update_records(patient,
                          record_type=data['type'], record_data=data['data'])

    elif transaction.type_ == "permission update":
        db.update_permissions(
            data['patient'], data['doctor'], data['perm'], data['perm_code'])

    elif transaction.type_ == 'account init':
        if data['user_type'] == 'doctor':
            db.save_doctor(data)
        elif data['user_type'] == 'patient':
            db.save_patient(data['public_key'], data['userid'])

    elif transaction.type_ == "appointment":
        db.save_appointment(transaction.data)

    elif transaction.type_ == 'log':
        pass

    elif transaction.type_ == 'appointment update':
        appointment_data = transaction.data
        user = {'user_type': 'doctor', 'userid': data['doctor']}
        appointments = db.get_user_appointments(user, 'all')
        required_appointments = [
            app for app in appointments
            if data['date'] == app['date'] and app['time'] == data['time']
            and app['patient'] == data['patient']
        ]
        for appointment in required_appointments:
            update = data['update']
            if appointment['approver'] == appointment_data['doctor']:
                if update == 'delete':
                    appointments = [app for app in appointments if app != appointment]
                elif update == 'approve':
                    appointment['approved'] = True
                    appointment['rejected'] = False
                elif update == 'reject':
                    appointment['approved'] = False
                    appointment['rejected'] = True
                db.update_appointment(appointment)
            else:
                return {'error': 'User not allowed to update'}


def load_all_blocks(db: database.Database, chain: Chain) -> None:
    """Load all blocks from the database into the chain, verifying integrity.

    Args:
        db: Database instance.
        chain: The chain to load blocks into.
    """
    blocks = db.get_all_blocks()

    for block in blocks:
        blk = Block()
        blk.header = block['block_header']
        blk.transactions = []

        transactions = block['transactions']
        transaction_hashes = []

        for transaction in transactions:
            expected_tr_hash = transaction['hash']
            tr = Transaction(transaction['type'], transaction['data'],
                             transaction['metadata'], hash='')

            if expected_tr_hash != create_hash_default(tr.data):
                print("Blockchain Transactions Invalid")
                sys.exit()

            transaction_hashes.append(tr.hash)
            blk.transactions.append(tr)

        expected_block_tr_data_hash = block['block_header']['data_hash']

        if expected_block_tr_data_hash != create_hash_default(transaction_hashes):
            print("Block TransactionHashes mismatch")
            sys.exit()

        chain.add_new_block(blk)
