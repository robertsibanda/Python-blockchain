from BlockChain.Security import verify_data, encrypt_data


class Person:
    
    def __init__(self, name, pk):
        self.name = name
        self.public_key = pk


class Patient(Person):
    
    def __init__(self, name, pk):
        super().__init__(name, pk)
        self.records = None  # load records from database


class HealthProfessional(Person):
    
    def __init__(self, name, organisation, role, pk, p_id):
        super().__init__(name, pk)
        self.organisation = organisation
        self.role = role
        self.p_id = p_id
    
    def verify_signature(self, signed_data, signature):
        return verify_data(signed_data, signature, self.public_key)
    
    def save(self, db):
        hp_details = {
            "name" : self.name,
            "pk"   : self.public_key,
            "role" : self.role,
            "practitioner_id" : self.p_id,
            "organisation_id" : self.organisation
        }
        
        db.save_practitioners(self.p_id, hp_details)
        
        
    
    
