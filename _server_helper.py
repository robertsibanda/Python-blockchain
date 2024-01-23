import sys
import threading
import rsa

import blockchain.blockchain
from blockchain.security import encrypt_data


def process_peer_chain_request(chain: blockchain.blockchain.Chain):
    return [block.header['hash'] for block in chain.chain]

    
def process_peer_registration(identity, signing_peer, new_node_chain_props, my_chain_props
                              ):
    if new_node_chain_props == my_chain_props:
        # chains are at the same level and are probably equal
        # send response notifying new node that chains at same level
        
        register_response = {"response": "chains-equal"}
        
        encrypted_response = ["register-response",
                              encrypt_data(rsa.PublicKey.load_pkcs1(signing_peer.pk),
                                           register_response
                                           )]
        
        signed_encrypted_response = identity.sign_data(encrypted_response)
        
        return f"{signed_encrypted_response}0000{encrypted_response}".encode('utf-8')
    
    if new_node_chain_props != my_chain_props:
        # check length of chain
        if my_chain_props["chain-length"] > new_node_chain_props["chain-length"]:
            # my chain is higher that new node chain
            # send response notifying of my chain size and other blocks
            register_response = {"response": "-chain"}
            encrypted_response = ["register-response",
                                  encrypt_data(rsa.PublicKey.load_pkcs1(signing_peer.pk),
                                               register_response
                                               )]
            signed_encrypted_response = identity.sign_data(encrypted_response)
            return f"{signed_encrypted_response}0000{encrypted_response}".encode('utf-8')
        
        elif my_chain_props["chain-length"] < new_node_chain_props["chain-length"]:
            # my chain is smaller than new node chain
            # request other missing blocks
            register_response = {"response": "+chain"}
            encrypted_response = ["register-response",
                                  encrypt_data(rsa.PublicKey.load_pkcs1(signing_peer.pk),
                                               register_response
                                               )]
            signed_encrypted_response = identity.sign_data(encrypted_response)
            return f"{signed_encrypted_response}0000{encrypted_response}".encode('utf-8')
        
        elif my_chain_props["chain-length"] == new_node_chain_props["chain-length"]:
            # chain size is the same with unmatching block hashes
            # one / all the chains are incorrect
            # check validity of chains
            register_response = {"response": "^hash"}
            encrypted_response = ["register-response",
                                  encrypt_data(rsa.PublicKey.load_pkcs1(signing_peer.pk),
                                               register_response
                                               )]
            signed_encrypted_response = identity.sign_data(encrypted_response)
            return f"{signed_encrypted_response}0000{encrypted_response}".encode('utf-8')
