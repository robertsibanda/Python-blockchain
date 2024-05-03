# store small amounts of data verifying data in the offchain

from blockchain.trasanction import Transaction
from blockchain.blockchain import Chain
from blockchain.block import Block
from blockchain.security import create_hash_default
from blockchain.storage import database

def get_patient_records(db, patient):
    # retrieve patient records from database
    return

def save_transaction(db: database.Database, transaction: Transaction):

    """
    save data that is inside a transaction
    used for creating database objects for new nodes
    """

    data = dict(transaction.data)

    if transaction.type == "record":

        patient = transaction.metadata['patient']

        db.update_records(patient,
            record_type=data['type'], record_data=data['data'])
    
    elif transaction.type == "permission update":
     
        db.update_permissions(data['patient'], data['doctor'], data['perm'], data['perm_code'])
    
    elif transaction.type == 'account init':
        if data['user_type'] == 'doctor':
            db.save_doctor(data)

        elif data['user_type'] == 'patient':
            db.save_patient(data['public_key'],data['userid'])

    elif transaction.type == "appointment":
     
        db.save_appointment(transaction.data)

    elif transaction.type == 'log':
        pass

    elif transaction.type == 'appointment update':
        
        appointment_data = transaction.data
        
        user = {
            'user_type' : 'doctor',
            'userid' : data['doctor']
        }
        appointments = db.get_user_appointments(user, 'all')
        required_appointments = [app for app in appointments
            if data['date'] == app['date'] and app['time'] == data['time']
                and app['patient'] == data['patient']]
                
        for appointment in required_appointments:
            print('Handling found : ', appointment)
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
                return { 'error' : 'User not allowed to update'}
        return

def load_all_blocks(db, chain: Chain):
        # load previously saved block from the database
        # verify and validate while loading
        blocks = db.get_all_blocks()

        for block in blocks:

            # verify block level data

            blk = Block()
            blk.header = block['block_header']
            blk.transactions = []
            
            transactions = block['transactions']
            transaction_hashes = list()

            for transaction in transactions:

                # verify transaction level data
                expected_tr_hash = transaction['hash']

                tr = Transaction(transaction['type'], transaction['data'],
                    transaction['metadata'], hash='')
                
                print(f"Comparing hashes {expected_tr_hash} \
                    and {create_hash_default(tr.data)}",
                      tr.hash == create_hash_default(tr.data))

                if expected_tr_hash != create_hash_default(tr.data):
                    # throw block invalid exception and delete block data and start again
                    print("Blockchain Transactions Invalid")
                    sys.exit()
                
                transaction_hashes.append(tr.hash)
                blk.transactions.append(tr)

            expected_block_tr_data_hash = block['block_header']['data_hash']

            # print(f"comparing {expected_block_tr_data_hash} and
            # {create_hash_default(transaction_hashes)} for {transaction_hashes}")

            if expected_block_tr_data_hash != create_hash_default(transaction_hashes):
                print("Block TransactionHashes mismatch")
                sys.exit()

            chain.add_new_block(blk)
