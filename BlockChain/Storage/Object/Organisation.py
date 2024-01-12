from BlockChain.Storage import Database


class Org:
    
    def __init__(self, database: Database.Database, organisation_id):
        self.database = database
        self.id = organisation_id
        self.pk = self.database.lookup_organisation(self.id)["organisation_pk"]
    
    def get_practitioner(self, practitioner_id):
        try:
            return self.database.lookup_practitioner(self.id, practitioner_id)
        except Exception as ex:
            print("Exception : " + str(ex))
            return None
    
    def add_new_member(self, details):
        """
        add new unverified member
        """
        pass
