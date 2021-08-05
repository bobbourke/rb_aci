class Tenant:

    def __init__(self, tenant, apic):

        self.controller = apic

        if type(tenant) == dict:
            self.name = tenant['name']
            self.description = tenant['descr']
            self.deployed = True
        else:
            self.name = tenant
            self.description = ""
            self.deployed = False
