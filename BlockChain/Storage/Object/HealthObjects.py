import datetime


class HealthObject:
    
    def __init__(self, name, uid, descption):
        self.name = name
        self.uid = uid
        self.descption = descption


class Record(HealthObject):
    def __init__(self, name, uid, descption, category):
        super().__init__(name, uid, descption)
        self.timestamp = datetime.datetime.now()
        self.category = category


class Allegie(Record):
    
    def __init__(self, name, uid, descption, category="allegic reaction"):
        super().__init__(name, uid, descption, category)


class Prescription(Record):
    
    def __init__(self, name, uid, descption, medicine, category="presciption"):
        super().__init__(name, uid, descption, category)
        self.medicine = medicine
        self.quantity = 1
    
    def is_patient_allegic(self, patient):
        pass
    
    def drug_to_drug_interaction(self, patient):
        pass
    
    def save(self):
        pass


class Disease(HealthObject):
    
    def __init__(self, name, uid, descption):
        super().__init__(name, uid, descption)


class Medicine(HealthObject):
    
    def __init__(self, name, uid, descption, chem, max_dose):
        super().__init__(name, uid, descption)
        self.chem = chem
        self.max_dose = max_dose


class LabResult(Record):
    
    def __init__(self, name, uid, descption, result, category="lab result"):
        super().__init__(name, uid, descption, category)
        self.result = result


class LabTest(HealthObject):
    
    def __init__(self, name, uid, descption):
        super().__init__(name, uid, descption)
