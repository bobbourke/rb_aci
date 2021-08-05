import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import time
from prettytable import PrettyTable

from .error_handling_class import check_error
from .tenant_class import Tenant


class Apic:

    def __init__(self, apic):

        """ Return a new instance of the APIC class.

        Arguments:

            apic - A dictionary which is used to create the class instance. It is the details for the APIC
                   which are passed to the class instance.
                    It has the following elements:
                        - name
                        - hostname
                        - username
                        - password
            base_url - URL required to access the API of the APIC
            token - When logging into APIC, it provides a token which can be used for default 600 seconds.
                    Once expired, the token requires refresh to continue session on APIC.
                    Token set to None and populated as part of APIC login.
            version - The APIC version. Set to None and populated at login.
            refresh_time - The time an ACI session is available for after login.
                           Set to None and populated at login.
                           Default value = 600 seconds (10 minutes)
            timer - User defined time which is the current time + the refresh time less 20%.
                    Used in Post , Get requests to compare the current time to this timer.
                    If current time < timer, then execute command.
                    If current time >= timer, then refresh token, then execute command.
        """

        self.name = apic['name']
        self.hostname = apic['hostname']
        self.username = apic['username']
        self.password = apic['password']

        self.base_url = "https://" + self.hostname + "/api/"
        self.token = None
        self.version = None
        self.refresh_time = None
        self.timer = None

    def login(self):

        """ Method that logs in to the APIC with the credentials from previous init method.

            Adds the login URL to the base URL.
            Completes the required payload with user credentials.

            Post request used to login.

            If request is successful, 200 OK returned and version, token and refresh time extracted.
            Timer is calculated based on the current time and the refresh time.

            If request is unsuccessful (any response code other than 200 OK),
            then error is checked by error handling class and exception raised.

            if method is successful, successful login to APIC is completed.
        """

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        url = self.base_url + "aaaLogin.json"

        payload = """{
                     "aaaUser" : {
                         "attributes" : {
                             "name" : "%s",
                             "pwd" : "%s"
                             }
                         }
                     }""" % (self.username, self.password)

        headers = {"Content-Type": "application/json"}
        request = requests.post(url, data=payload, headers=headers, verify=False)
        if request.status_code == 200:
            output = json.loads(request.text)
            output = output['imdata'][0]['aaaLogin']['attributes']
            self.version = output['version']
            self.token = output['token']
            self.refresh_time = int(output["refreshTimeoutSeconds"])
            self.timer = time.time() + (self.refresh_time - (self.refresh_time * 0.2))
        else:
            error = check_error(request)
            raise error

    def refresh_token(self):

        """ If the APIC has been logged in for approximately 8 minutes, it will be using the same token.
            This token expires after 10 minutes so if a request is pushed to the APIC after 8 minutes,
            then the token is refreshed before the request is processed.

            Once this method is run a new token is returned which can be used for another 10 minutes.
            The refresh time is returned again from the APIC and a new timer is worked out which is
            8 minutes from this request.

            Any response code other than 200 OK is checked for errors and an exception is raised.

        """

        print("** Token Refresh **")

        headers = {'Authorization': "Bearer " + self.token,
                   'Cookie': "APIC-cookie=" + self.token}

        url = self.base_url + "aaaRefresh.json"

        request = requests.get(url, headers=headers, verify=False)

        if request.status_code == 200:
            output = json.loads(request.text)
            output = output['imdata'][0]['aaaLogin']['attributes']
            self.token = output['token']
            self.refresh_time = int(output['refreshTimeoutSeconds'])
            self.timer = time.time() + (self.refresh_time - (self.refresh_time * 0.2))
        else:
            error = check_error(request)
            raise error

    def get_request(self, url):

        if time.time() >= self.timer:
            self.refresh_token()

        headers = {'Authorization': "Bearer " + self.token,
                   'Cookie': "APIC-cookie=" + self.token}

        url = self.base_url + url
        request = requests.get(url, headers=headers, verify=False)

        if request.status_code == 200:
            output = json.loads(request.text)
            output = output['imdata']
            return output
        else:
            error = check_error(request)
            raise error

    def tenants(self):

        url = "class/fvTenant.json"

        output = self.get_request(url)

        tenants = []
        for i in output:
            tenant = i['fvTenant']['attributes']
            tenant = Tenant(tenant, self)
            tenants.append(tenant)

        return tenants

    def fabric_devices(self, format_table=False):

        url = "node/class/topSystem.json?order-by=topSystem.id|asc"

        devices = self.get_request(url)

        fabric_devices = []

        for device in devices:
            dev_id = device['topSystem']['attributes']['id']
            name = device['topSystem']['attributes']['name']
            role = device['topSystem']['attributes']['role']
            pod_id = device['topSystem']['attributes']['podId']
            state = device['topSystem']['attributes']['state']

            url = "node/mo/topology/pod-{0}/node-{1}.json".format(pod_id, dev_id)
            devices_ = self.get_request(url)

            model = None
            for device_ in devices_:
                model = device_['fabricNode']['attributes']['model']

            fabric_device = {"ID": dev_id, "Name": name, "Role": role, "Model": model, "Pod ID": pod_id, "State": state}

            fabric_devices.append(fabric_device)

        if fabric_devices:
            if format_table:
                table = PrettyTable()
                table.field_names = ["ID", "Name", "Role", "Model", "Pod ID", "State"]
                table.title = "ACI Fabric Devices - {0}".format(self.name)

                for aci_device in fabric_devices:
                    table.add_row([aci_device['ID'], aci_device['Name'], aci_device['Role'], aci_device['Model'],
                                   aci_device['Pod ID'], aci_device['State']])
                return table
            else:
                return fabric_devices
        else:
            return

    def cluster_health(self, format_table=False):

        url = "node/class/infraWiNode.json"

        apics = self.get_request(url)

        apics_details = []

        for apic in apics:
            name = apic['infraWiNode']['attributes']['nodeName']
            pod_id = apic['infraWiNode']['attributes']['podId']
            health = apic['infraWiNode']['attributes']['health']
            mode = apic['infraWiNode']['attributes']['apicMode']
            op_status = apic['infraWiNode']['attributes']['operSt']
            admin_state = apic['infraWiNode']['attributes']['adminSt']
            ip_address = apic['infraWiNode']['attributes']['addr']

            apic_details = {"Name": name, "Pod ID": pod_id, "Health": health, "Mode": mode, "Op_Status": op_status,
                            "Admin_State": admin_state, "IP Address": ip_address}
            if apic_details not in apics_details:
                apics_details.append(apic_details)

        if apics_details:
            if format_table:
                table = PrettyTable()
                table.field_names = ["APIC Name", "POD ID", "Health", "Mode", "Operational State", "Admin State",
                                     "IP Address"]
                table.title = "ACI APIC Cluster Health - {0}".format(self.name)

                for apic_ in apics_details:
                    table.add_row([apic_['Name'], apic_['Pod ID'], apic_['Health'], apic_['Mode'], apic_['Op_Status'],
                                   apic_['Admin_State'], apic_['IP Address']])
                return table
            else:
                return apics_details
        else:
            return

    def license_status(self, format_table=False):

        url = "node/class/licensePermLicReserve.json"

        lic_detail = None
        lic_details = self.get_request(url)

        for lic_detail_ in lic_details:
            status = lic_detail_['licensePermLicReserve']['attributes']['authStatus']
            reg_status = lic_detail_['licensePermLicReserve']['attributes']['registerState']
            lic_detail = {"Status": status, "Registration Status": reg_status}

        if lic_detail:
            if format_table:
                table = PrettyTable()
                table.field_names = ['Status', 'Registration Status']
                table.title = "ACI Fabric License Status - {0}".format(self.name)

                table.add_row([lic_detail['Status'], lic_detail['Registration Status']])

                return table
            else:
                return lic_detail
        else:
            return
