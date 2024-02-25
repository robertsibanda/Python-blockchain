import blockchain.blockchain
from blockchain.blockchain import Chain
from blockchain.peer import Peer


def process_peer_chain_request(chain: blockchain.blockchain.Chain):
    return [block.header['hash'] for block in chain.chain]


def process_close_block(transaction_queue: list, transactions):
    
    transaction_hashes = [tr.hash for tr in transaction_queue]
    found_hash = [tr in transaction_hashes for tr in transactions]
    
    new_block_transactions = []
    
    if found_hash.count(False) > 0:
        # some transactions not found
        # request from other nodes
        return {"found": False}
    
    for tr in transaction_queue:
        for tr2 in transaction_hashes:
            if tr == tr2:
                new_block_transactions.append(tr)
                transaction_queue.remove(tr)
                
    return {"transactions": new_block_transactions, "found": True}


def new_node_regiser(new_node_props: dict, chain: Chain, peer: Peer,
                     chains_to_validate: dict):
    
    my_chain_props = {
        "chain-length": str(len(chain.chain)),
        "last-block": chain.get_last_block().header['hash']}

    if new_node_props[1] == my_chain_props:
        return {"response": "chains-equal"}

    if new_node_props != my_chain_props:
        if my_chain_props["chain-length"] > new_node_props[1]["chain-length"]:
            return {"response": "-chain"}

        if my_chain_props["chain-length"] < new_node_props[1]["chain-length"]:
            # TODO work on copying chain
            return {"response": "+chain"}
        
        if my_chain_props["last-block"] != new_node_props[1]["last-block"]:
            return {"response": "^hash"}
    

    
