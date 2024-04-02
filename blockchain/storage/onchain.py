# store small amounts of data verifying data in the offchain
from blockchain.trasanction import Transaction
from blockchain.blockchain import Chain
from blockchain.block import Block
from blockchain.security import create_hash_default


def save_transaction(db, transaction: Transaction):

    """
    save data that is inside a transaction
    used for creating database objects for new nodes
    """

    data = transaction.data

    if transaction.type == "record":

        patient = db.find_patient(transaction.metadata['patient'])

        db.update_records(patient=patient,
            record_type=data['type'], record_data=data['data'])
    
    if transaction.type == "permission update":

        patient = db.find_patient(data['patient'])
        
        db.update_permissions(patient['public_key'], 
            data['permissions', data['doctor']])
    
    if transaction.type == 'account init':

        if data['user_type'] == 'doctor':
            db.save_doctor(data['public_key'])

        elif data['user_type'] == 'patient':
            db.save_patient(data['public_key'])



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
                                 transaction['metadata'], transaction['hash'])
                
                print(f"Comparing hashes {expected_tr_hash} and {create_hash_default(tr.data)}",
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

            chain.chain.append(blk)