#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
(c) 2015, David Symons (Multimac) <Mult1m4c@gmail.com>
(c) 2016, Konstantin Shalygin <k0ste@cn.ru>
(c) 2016, Hitesh Prabhakar <HP41@GitHubm>

This file is part of Ansible

This module is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this software.  If not, see <http://www.gnu.org/licenses/>.
"""


# ===========================================


DOCUMENTATION = '''
---
module: cups_lpadmin
author:
    - "David Symons (Multimac) <Mult1m4c@gmail.com>"
    - "Konstantin Shalygin <k0ste@k0ste.ru>"
    - "Hitesh Prabhakar <H41P@GitHub>"
short_description: Manages printers in CUPS printing system.
description:
    - Creates, removes and sets options for printers in CUPS.
    - Creates, removes and sets options for classes in CUPS.
    - For class installation, the members are defined as a final state and therefore will only have the members defined.
    - At the moment, this module doesn't support check_mode
version_added: "2.2"
notes: []
requirements:
    - CUPS 1.7+
options:
    name:
        description:
            - Name of the printer in CUPS.
        required: false
        default: null
    purge:
        description:
            - Task to purge all printers in CUPS. Convenient before deploy.
        required: false
        default: false
        choices: ["true", "false"]
    state:
        description:
            - Whether the printer should or not be in CUPS.
        required: false
        default: present
        choices: ["present", "absent"]
    printer_or_class:
        description:
            - State whether the object we are working on is a printer or class.
        required: false
        default: printer
        choices: ["printer", "class"]
    driver:
        description:
            - System V interface or PPD file.
        required: false
        default: model
        choices: ["model", "ppd"]
    uri:
        description:
            - The URI to use when connecting to the printer. This is only required in the present state.
        required: false
        default: null
    enabled:
        description:
            - Whether or not the printer should be enabled and accepting jobs.
        required: false
        default: true
        choices: ["true", "false"]
    shared:
        description:
            - Whether or not the printer should be shared on the network.
        required: false
        default: false
        choices: ["true", "false"]
    model:
        description:
            - The System V interface or PPD file to be used for the printer.
        required: false
        default: null
    default:
        description:
          - Set default server printer. Only one printer can be default.
        required: false
        default: false
        choices: ["true", "false"]
    info:
        description:
            - The textual description of the printer.
        required: false
        default: null
    location:
        description:
            - The textual location of the printer.
        required: false
        default: null
    assign_cups_policy:
        description:
            - Assign a policy defined in /etc/cups/cupsd.conf to this printer.
        required: false
        default: null
    class_members:
        description:
            - A list of printers to be added to this class.
        required: false
        default: []
        type: list
    report_ipp_supply_levels:
        description:
            - Whether or not the printer must report supply status via IPP.
        required: false
        default: true
        choices: ["true", "false"]
    report_snmp_supply_levels:
        description:
            - Whether or not the printer must report supply status via SNMP (RFC 3805).
        required: false
        default: true
        choices: ["true", "false"]
    job_kb_limit:
        description:
            - Limit jobs to this printer (in KB)
        required: false
        default: null
    job_quota_limit:
        description:
            - Sets the accounting period for per-user quotas. The value is an integer number of seconds.
        required: false
        default: null
    job_page_limit:
        description:
            - Sets the page limit for per-user quotas. The value is the integer number of pages that can be printed.
            - Double sided pages are counted as 2.
        required: false
        default: null
    options:
        description:
            - A dictionary of key-value pairs describing printer options and their required value.
        default: {}
        required: false
'''


# ===========================================


EXAMPLES = '''
# Creates HP printer via ethernet, set default paper size and
  make this printer as server default
- cups_lpadmin:
    name: 'HP_M1536'
    state: 'present'
    printer_or_class: 'printer'
    uri: 'hp:/net/HP_LaserJet_M1536dnf_MFP?ip=192.168.1.2'
    model: 'drv:///hp/hpcups.drv/hp-laserjet_m1539dnf_mfp-pcl3.ppd'
    default: 'true'
    location: 'Lib'
    info: 'MFP'
    printer_assign_policy: 'students'
    report_ipp_supply_levels: 'true'
    report_snmp_supply_levels: 'false'
    options:
      media: 'iso_a4_210x297mm'

# Creates HP Printer via IPP (shared USB printer in another CUPS instance)
  very important include 'snmp=false' to prevent adopt 'parent' driver,
  because if 'parent' receive not raw job this job have fail (filter failed)
- cups_lpadmin:
    name: 'HP_P2055'
    state: 'present'
    uri: 'ipp://192.168.2.127:631/printers/HP_P2055?snmp=false'
    model: 'raw'
    default: 'true'
    options:
      media: 'iso_a4_210x297mm'

# Create CUPS Class
- cups_lpadmin:
    name: 'TestClass'
    state: 'present'
    printer_or_class: 'class'
    class_members:
        - TestPrinter1
        - TestPrinter2
    info: 'A test class'
    location: 'A place of great importance'

# Creates a Zebra ZPL printer called zebra
- cups_lpadmin: state=present name=zebra uri=192.168.1.2 model=drv:///sample.drv/zebra.ppd

# Updates the zebra printer with some custom options, will use lpd when no method is defined.
- cups_lpadmin:
    state: present
    printer_or_class: printer
    name: zebra
    uri: 192.168.1.2
    model: drv:///sample.drv/zebra.ppd
    job_kb_limit: 2048
    job_quota_limit: 86400
    job_page_limit: 10
    options:
      PageSize: w288h432

# Deletes the printers/classes set up by the previous tasks
- cups_lpadmin: state=absent printer_or_class=printer name=zebra
- cups_lpadmin: state=absent printer_or_class=class name=TestClass
'''


# ===========================================


RETURN = '''
state:
    description: The state as defined in the invocation of this script.
    returned: always
    type: string
    sample: "present"
printer_or_class:
    description: Printer or Class as defined when this script was invoked.
    returned: always
    type: string
    sample: "class"
name:
    description: The name of the destination (printer/class) as defined when the script was invoked.
    returned: always
    type: string
    sample: "Test-Printer"
changed:
    description: If any changes were made to the system when this script was run.
    returned: always
    type: boolean
    sample: False
stdout:
    description: Output from all the commands run concatenated. Only returned if any changes to the system were run.
    returned: changed
    type: boolean
    sample: "sample_command_output"
stderr:
    description: Any output errors from any commands run. Only returned if any changes to the system were run.
    returned: failed
    type: string
    sample: "sample_command_error_output"
'''


# ===========================================


class CUPSObject(object):
    """
        This is the main class that directly deals with the lpadmin command.

        Method naming methodology:
            - Methods prefixed with 'cups_object' or '_cups_object' can be used with both printer and classes.
            - Methods prefixed with 'class' or '_class' are meant to work with classes only.
            - Methods prefixed with 'printer' or '_printer' are meant to work with printers only.

        CUPSObject handles printers like so:
            - If state=absent,
                - Printer exists: Deletes printer
                - Printer doesn't exist: Does nothing and exits
            - If state=present:
                - Printer exists: Checks printer options and compares them to the ones stated:
                    - Options are different: Deletes the printer and installs it again with stated options.
                    - Options are same: Does nothing and exits.
                - Printer doesn't exist: Installs printer with stated options.
            - Mandatory options are set every time if the right variables are defined. They are:
                - cupsIPPSupplies
                - cupsSNMPSupplies
                - printer-op-policy
                - job-k-limit
                - job-page-limit
                - job-quota-period

        CUPSObject handles classes like so:
            - If state=absent:
                - Class exists: Deletes class
                - Class doesn't exist: Does nothing and exits
            - If state=present:
                - Class exists: Checks class options and members and compares them to the ones stated:
                    - Options and members are different: Deletes the class and installs it again with
                      stated options and stated members.
                    - Options and members are same: Does nothing and exits.
                - Class doesn't exist: Installs class with stated options and members.
            - Mandatory options are set every time if the right variables are defined. They are:
                - cupsIPPSupplies
                - cupsSNMPSupplies
                - printer-op-policy
            - Notes about how classes are handled:
                - Members stated will be the final list of printers in that class.
                - It cannot add or remove printers from an existing list that might have more/other members defined.
                - It'll uninstall the class and create it from scratch as defined in this script if the defined member
                  list and the actual member list don't match.
    """

    def __init__(self, module):
        """
        Assigns module vars to object
        """
        self.module = module

        self.driver = self.strip_whitespace(module.params['driver'])
        self.name = self.strip_whitespace(module.params['name'])

        self.purge = module.params['purge']

        self.uri = self.strip_whitespace(module.params['uri'])

        self.enabled = module.params['enabled']
        self.shared = module.params['shared']
        self.default = module.params['default']

        self.model = self.strip_whitespace(module.params['model'])

        self.info = self.strip_whitespace(module.params['info'])
        self.location = self.strip_whitespace(module.params['location'])

        self.options = module.params['options']

        self.assign_cups_policy = self.strip_whitespace(module.params['assign_cups_policy'])

        self.class_members = module.params['class_members']

        self.report_ipp_supply_levels = module.params['report_ipp_supply_levels']
        self.report_snmp_supply_levels = module.params['report_snmp_supply_levels']
        self.job_kb_limit = module.params['job_kb_limit']
        self.job_quota_limit = module.params['job_quota_limit']
        self.job_page_limit = module.params['job_page_limit']

        # Use lpd if a protocol is not specified
        if self.uri and ':/' not in self.uri:
            self.uri = 'lpd://{0}/'.format(self.uri)

        if (module.params['state'] is 'present') and (module.params['printer_or_class'] is None):
            module.fail_json(msg="When state=present printer or class must be defined.")

    @staticmethod
    def strip_whitespace(text):
        """
        A static method to help with stripping white space around object variables
        :returns: Trailing whitespace removed text or 'None' if input is 'None'.
        """
        return text.strip() if text else None

    def _printer_get_installed_drivers(self):
        """
        Parses the output of lpinfo -l -m to provide a list of available drivers on machine

        Example output from lpinfo -l -m:
        Model:  name = gutenprint.5.2://xerox-wc_m118/expert
                natural_language = en
                make-and-model = Xerox WorkCentre M118 - CUPS+Gutenprint v5.2.11
                device-id = MFG:XEROX;MDL:WorkCentre M118;DES:XEROX WorkCentre M118;

        The output is parsed into a hash and then placed into the value of another hash where the key is the name field:
        'gutenprint.5.2://xerox-wc_m118/expert': 'name': 'gutenprint.5.2://xerox-wc_m118/expert'
                                                 'natural_language': 'en'
                                                 'make-and-model': 'Xerox WorkCentre M118 - CUPS+Gutenprint v5.2.11'
                                                 'device-id': 'MFG:XEROX;MDL:WorkCentre M118;DES:XEROX WorkCentre M118;'

        :returns: Hash defining all the drivers installed on the system.
        """
        cmd = ['lpinfo', '-l', '-m']
        (rc, out, err) = self.module.run_command(cmd)

        # We want to split on sections starting with "Model:" as that specifies a new available driver
        prog = re.compile("^Model:", re.MULTILINE)
        cups_drivers = re.split(prog, out)

        drivers = {}
        for d in cups_drivers:

            # Skip if the line contains only whitespace
            if not d.strip():
                continue

            curr = {}
            for l in d.splitlines():
                kv = l.split('=', 1)

                # Strip out any excess whitespace from the key/value
                kv = map(str.strip, kv)

                curr[kv[0]] = kv[1]

            # Store drivers by their 'name' (i.e. path to driver file)
            drivers[curr['name']] = curr

        return drivers

    def _printer_get_all_printers(self):
        """
        Method return current printers in CUPS.
        """
        cmd = ['lpstat', '-a']
        (rc, out, err) = self.module.run_command(cmd)

        if rc == 0:
            # Match only 1st column, where placed printer name
            all_printers = [out.split()[0] for out in out.splitlines()]
            return all_printers
        elif rc == 1:
            return

    def _printer_purge_all_printers(self):
        """
        Purge all returned devices in _printer_get_all_printers method.

        If no one printer returned - exit.
        """
        all_printers = self._printer_get_all_printers()

        if not all_printers:
            self.module.exit_json(msg="No printers")
        else:
            for printer in all_printers:
                (rc, out, err) = self._cups_object_uninstall(another_cups_object_to_uninstall=printer)
            return rc, out, err

    def _printer_get_make_and_model(self):
        """
        Method to return the make and model of the driver/printer that is supplied to the object.

        if ppd is provided, ignore this as the ppd provided takes priority over finding a driver.

        If not ppd is provided (default behaviour), the model specified is used.
        It checks to see if the model specified is in the list of drivers installed on the system. If not, the whole
        module fails out with an error message.

        :returns: make-and-model of the model specified.
        """
        if self.driver == 'model':
            # Raw printer is defined
            if self.model == None or self.model == 'raw':
                return "Remote Printer"
        elif self.driver == 'ppd':
            return

        installed_drivers = self._printer_get_installed_drivers()

        if self.model in installed_drivers:
            return installed_drivers[self.model]['make-and-model']

        self.module.fail_json(msg="Unable to determine printer make and model {0}".format(self.model))

    def _printer_install(self):
        """
        Installs the printer with the settings defined.

        :returns: rc, out, err. The output of the lpadmin installation command.
        """
        cmd = ['lpadmin', '-p', self.name, '-v', self.uri]

        if self.enabled:
            cmd.append('-E')

        if self.shared:
            cmd.extend(['-o', 'printer-is-shared=true'])
        else:
            cmd.extend(['-o', 'printer-is-shared=false'])

        if self.driver == 'model' and self.model != None:
            cmd.extend(['-m', self.model])
        elif self.driver == 'ppd':
            cmd.extend(['-P', self.model])

        if self.info:
            cmd.extend(['-D', self.info])

        if self.location:
            cmd.extend(['-L', self.location])

        if self.default:
            cmd.extend(['-d', self.name])

        return self.module.run_command(cmd)

    def _printer_install_mandatory_options(self):
        """
        Installs mandatory printer options.

        cupsIPPSupplies, cupsSNMPSupplies, job-k-limit, job-page-limit, printer-op-policy,job-quota-period
        cannot be checked via cups command-line tools yet. Therefore force set these options if they are defined.
        If there's an error running the command, the whole module will fail with an error message.
        """
        orig_cmd = ['lpadmin', '-p', self.name]
        cmd = list(orig_cmd)  # Making a copy of the list/array

        if self.report_ipp_supply_levels:
            cmd.extend(['-o', 'cupsIPPSupplies=true'])
        else:
            cmd.extend(['-o', 'cupsIPPSupplies=false'])

        if self.report_snmp_supply_levels:
            cmd.extend(['-o', 'cupsSNMPSupplies=true'])
        else:
            cmd.extend(['-o', 'cupsSNMPSupplies=false'])

        if self.job_kb_limit:
            cmd.extend(['-o', 'job-k-limit={0}'.format(self.job_kb_limit)])

        if self.job_page_limit:
            cmd.extend(['-o', 'job-page-limit={0}'.format(self.job_page_limit)])

        if self.job_quota_limit:
            cmd.extend(['-o', 'job-quota-period={0}'.format(self.job_quota_limit)])

        if self.assign_cups_policy:
            cmd.extend(['-o', 'printer-op-policy={0}'.format(self.assign_cups_policy)])

        if cmd != orig_cmd:
            (rc, out, err) = self.module.run_command(cmd)
            if err:
                message = "Installing mandatory options for printer if defined. " \
                          "{0} couldn't run. " \
                          "Error details - {1}".format(cmd, err)
                self.module.fail_json(msg=message)

    def _printer_install_options(self):
        """
        Installs any printer driver specific options defined.
        :returns: rc, out, err. The output of the lpadmin installation command.
        """
        cmd = ['lpadmin', '-p', self.name]

        for k, v in self.options.iteritems():
            cmd.extend(['-o', '{0}={1}'.format(k, v)])

        if self.default:
            cmd.extend(['-d', self.name])

        return self.module.run_command(cmd)

    def _class_install(self):
        """
        Installs the class with the settings defined.

        It loops through the list of printers that are supposed to be in the class and confirms if they exists and
        adds them to the class. If any one of the printers don't exist, the whole module will fail with an error
        message.

        :returns: rc, out, err. The output of the lpadmin installation command.
        """
        rc = None
        out = ''
        err = ''
        for printer in self.class_members:
            # Going through all the printers that are supposed to be in the class and adding them to said class.
            # Ensuring first the printer exists.
            if self.exists(another_cups_object_to_check=printer):
                (rc, install_out, install_err) = self.module.run_command(['lpadmin', '-p', printer, '-c', self.name])
                out = (out + '\n' + install_out).strip('\n')
                err = (err + '\n' + install_err).strip('\n')
            else:
                message = "Printer {0} doesn't exist and cannot be added to class {1}".format(printer, self.name)
                self.module.fail_json(msg=message)

        # Now that the printers are added to the class and the class created, we are setting up a few
        # settings for the class itself.
        if self.exists():
            cmd = ['lpadmin', '-p', self.name]

            if self.enabled:
                cmd.append('-E')

            if self.shared:
                cmd.extend(['-o', 'printer-is-shared=true'])
            else:
                cmd.extend(['-o', 'printer-is-shared=false'])

            if self.info:
                cmd.extend(['-D', self.info])

            if self.location:
                cmd.extend(['-L', self.location])

            (rc, install_out, install_err) = self.module.run_command(cmd)
            out = (out + '\n' + install_out).strip('\n')
            err = (err + '\n' + install_err).strip('\n')

        return rc, out, err

    def _class_install_mandatory_options(self):
        """
        Installs mandatory class options.

        cupsIPPSupplies, cupsSNMPSupplies, printer-op-policy,job-quota-period cannot be checked via
        cups command-line tools yet. Therefore force set these options if they are defined.
        If there's an error running the command, the whole module will fail with an error message.
        """
        orig_cmd = ['lpadmin', '-p', self.name]
        cmd = list(orig_cmd)  # Making a copy of the list/array

        if self.report_ipp_supply_levels:
            cmd.extend(['-o', 'cupsIPPSupplies=true'])
        else:
            cmd.extend(['-o', 'cupsIPPSupplies=false'])

        if self.report_snmp_supply_levels:
            cmd.extend(['-o', 'cupsSNMPSupplies=true'])
        else:
            cmd.extend(['-o', 'cupsSNMPSupplies=false'])

        if self.assign_cups_policy:
            cmd.extend(['-o', 'printer-op-policy={0}'.format(self.assign_cups_policy)])

        if cmd != orig_cmd:
            (rc, out, err) = self.module.run_command(cmd)
            if err:
                message = "Installing mandatory options for class if defined. " \
                          "{0} couldn't run. " \
                          "Error details - {1}".format(cmd, err)
                self.module.fail_json(msg=message)

    def _cups_object_uninstall(self, another_cups_object_to_uninstall=None):
        """
        Uninstalls a printer or class

        :param another_cups_object_to_uninstall: Optional param to uninstall another printer.
        :returns: rc, out, err. The output of the lpadmin uninstallation command.
        """
        cmd = ['lpadmin', '-x']

        if another_cups_object_to_uninstall is None:
            cmd.append(self.name)
        else:
            cmd.append(another_cups_object_to_uninstall)

        return self.module.run_command(cmd)

    def exists(self, another_cups_object_to_check=None):
        """
        Checks to see if a printer or class exists.

        Using the lpstat command and based on if an error code is returned it can confirm if a printer or class exists.

        :param another_cups_object_to_check: Optional param to check if another printer or class exists.
        :returns: True of return code form the command is 0 and therefore there where no errors and printer/class
        exists.
        """
        cmd = ['lpstat', '-p']

        if another_cups_object_to_check is None:
            cmd.append(self.name)
        else:
            cmd.append(another_cups_object_to_check)

        (rc, out, err) = self.module.run_command(cmd)
        return rc == 0

    def cups_object_get_cups_options(self):
        """
        Returns a list of currently set options for the printer or class.

        Uses lpoptions -p command to list all the options, eg:
            copies=1 device-uri=socket://127.0.0.1:9100 finishings=3 job-cancel-after=10800
            job-hold-until=no-hold job-priority=50 job-sheets=none,none marker-change-time=0 number-up=1
            printer-commands=AutoConfigure,Clean,PrintSelfTestPage printer-info='HP LaserJet 4250 Printer Info'
            printer-is-accepting-jobs=true printer-is-shared=true printer-location=PrinterLocation
            printer-make-and-model='HP LaserJet 4250 Postscript (recommended)' printer-state=3
            printer-state-change-time=1463902120 printer-state-reasons=none printer-type=8425668
            printer-uri-supported=ipp://localhost/printers/TestPrinter

        :returns: A hash of the above info.
        """
        cmd = ['lpoptions', '-p', self.name]
        (rc, out, err) = self.module.run_command(cmd)

        options = {}
        for s in shlex.split(out):
            kv = s.split('=', 1)

            if len(kv) == 1:  # If we only have an option name, set it's value to None
                options[kv[0]] = None
            elif len(kv) == 2:  # Otherwise set it's value to what we received
                options[kv[0]] = kv[1]

        return options

    def printer_check_cups_options(self):
        """
        Creates a hash of the defined options sent to this module.
        Polls and retrieves a hash of options currently set for the printer.
        Compares them and returns True if the option values are satisfied or False if not satisfied.

        :returns: 'True' if the option values match else 'False'
        """
        expected_cups_options = {
            'device-uri': self.uri,
            'printer-make-and-model': self._printer_get_make_and_model(),
            'printer-location': self.location,
            'printer-is-shared': 'true' if self.shared else 'false',

            # 'printer-info' defaults to the printer name if not specified manually
            'printer-info': self.info if self.info else self.name,
        }

        cups_options = self.cups_object_get_cups_options()

        # Comparing expected options as stated above to the options of the actual printer object.
        for k in expected_cups_options:
            if k not in cups_options:
                return False

            if expected_cups_options[k] != cups_options[k]:
                return False

        return True

    def class_check_cups_options(self):
        """
        Creates a hash of the defined options sent to this module.
        Polls and retrieves a hash of options currently set for the class.
        Compares them and returns True if the option values are satisfied or False if not satisfied.

        :returns: 'True' if the option values match else 'False'
        """
        expected_cups_options = {
            'printer-location': self.location,
        }

        if self.info:
            expected_cups_options['printer-info'] = self.info

        options = self.cups_object_get_cups_options()
        options_status = True

        # Comparing expected options as stated above to the options of the actual class object.
        for k in expected_cups_options:
            if k not in options:
                options_status = False
                break

            if expected_cups_options[k] != options[k]:
                options_status = False
                break

        # Comparing expected class members and actual class members
        class_members_status = sorted(self.class_members) == sorted(self.class_get_current_members())

        return options_status and class_members_status

    def class_get_current_members(self):
        """
        Uses the lpstat -c command to get a list of members, eg:
        members of class TestClass:
            TestPrinter1
            TestPrinter2

        This is parsed into a list. The first line is skipped.

        :returns: A list of members for class specified in the module.
        """
        cmd = ['lpstat', '-c', self.name]
        (rc, out, err) = self.module.run_command(cmd)

        if err:
            self.module.fail_json(
                msg="Error occurred while trying to 'lpstat' class - {0} - {1}".format(self.name, err))

        members = []
        temp = shlex.split(out)
        # Skip first line as it's an information line.
        temp = temp[1:]
        for m in temp:
            str.strip(m)
            members.append(m)

        return members

    def printer_get_specific_options(self):
        """
        Returns a hash of printer specific options with its current value, available values and its label.
        Runs lpoptions -p <printer_name> -l, eg:
            HPCollateSupported/Collation in Printer: True288 *False288
            HPOption_500_Sheet_Feeder_Tray3/Tray 3: *True False
            HPOption_Duplexer/Duplex Unit: *True False
            HPOption_Disk/Printer Disk: True *False
            HPOption_PaperPolicy/Paper Matching: *Prompt Scale Crop
            HPServicesWeb/Services on the Web: *SupportAndTroubleshooting ProductManuals ColorPrintingAccessUsage
                OrderSupplies ShowMeHow
            HPServicesUtility/Device Maintenance: *DeviceAndSuppliesStatus
            Resolution/Printer Resolution: *600dpi 1200dpi
            PageSize/Page Size: *Letter Legal Executive HalfLetter w612h936 4x6 5x7 5x8 A4 A5 A6 RA4 B5 B6 W283H425
                w553h765 w522h737 w558h774 DoublePostcard Postcard Env10 Env9 EnvMonarch EnvISOB5 EnvC5 EnvC6 EnvDL
                Custom.WIDTHxHEIGHT
            InputSlot/Paper Source: *Auto Tray1 Tray2 Tray3 Tray1_Man
            Duplex/2-Sided Printing: *None DuplexNoTumble DuplexTumble
            Collate/Collate: True *False

        This is parsed into a hash with option name as key and value with currently selected option,
        label of the option and available values eg:
            'HPCollateSupported': 'current': 'False288'
                                  'label': 'Collation in Printer'
                                  'values': 'True288'
                                            'False288'

        :returns: A hash of printer options. It includes currently set option and other available options.
        """
        cmd = ['lpoptions', '-p', self.name, '-l']
        (rc, out, err) = self.module.run_command(cmd)

        options = {}
        for l in out.splitlines():
            remaining = l

            (name, remaining) = remaining.split('/', 1)
            (label, remaining) = remaining.split(':', 1)

            values = shlex.split(remaining)

            current_value = None
            for v in values:
                # Current value is prepended with a '*'
                if not v.startswith('*'):
                    continue

                v = v[1:]  # Strip the '*' from the value

                current_value = v
                break

            options[name] = {
                'current': current_value,
                'label': label,
                'values': values,
            }

        return options

    def printer_check_options(self):
        """
        Returns if the defined options is the same as the options currently set for the printer.
        :returns: Returns if the defined options is the same as the options currently set for the printer.
        """
        expected_printer_options = self.options

        printer_options = self.printer_get_specific_options()
        for k in expected_printer_options:
            if k not in printer_options:
                return False

            if expected_printer_options[k] != printer_options[k]['current']:
                return False

        return True

    def printer_install(self):
        """
        The main method that's called when state=present and printer_or_class=printer

        It checks to see if printer exists and if its settings are the same as defined.
        If not, it deletes it.

        It then checks to see if it exists again and installs it with defined settings if it doesn't exist.

        It also installs mandatory settings.

        Lastly it sets the printer specific options to the printer if it isn't the same.
        :returns: rc, out, err. The output of the multiple commands run during this installation process.
        """
        if self.uri is None and not self.exists():
            self.module.fail_json(msg="'URI' is required to install printer")

        rc = None
        out = ''
        err = ''

        if self.exists() and not self.printer_check_cups_options():
            (rc, uninstall_out, uninstall_err) = self._cups_object_uninstall()

            out = (out + '\n' + uninstall_out).strip('\n')
            err = (err + '\n' + uninstall_err).strip('\n')

        if not self.exists():
            (rc, install_out, install_err) = self._printer_install()

            out = (out + '\n' + install_out).strip('\n')
            err = (err + '\n' + install_err).strip('\n')

        # cupsIPPSupplies, cupsSNMPSupplies, job-k-limit, job-page-limit, printer-op-policy,
        # job-quota-period cannot be checked via cups command-line tools yet.
        # Therefore force set these options if they exist
        if self.exists():
            self._printer_install_mandatory_options()

        if not self.printer_check_options():
            (rc, options_out, options_err) = self._printer_install_options()

            out = (out + '\n' + options_out).strip('\n')
            err = (err + '\n' + options_err).strip('\n')

        return rc, out, err

    def cups_object_purge(self):
        """
        """
        rc = None
        out = ''
        err = ''

        (rc, out, err) = self._printer_purge_all_printers()

        return rc, out, err

    def cups_object_uninstall(self):
        """
        Uninstalls a printer or class.
        :returns: rc, out, err. The output of the uninstallation command.
        """
        rc = None
        out = ''
        err = ''

        if self.exists():
            (rc, out, err) = self._cups_object_uninstall()

        return rc, out, err

    def class_install(self):
        """
        The main method that's called when state=present and printer_or_class=class

        It checks to see if class exists and if its settings are the same as defined.
        If not, it deletes it.

        It then checks to see if it exists again and installs it with defined settings if it doesn't exist.

        It also installs mandatory settings.

        :returns: rc, out, err. The output of the multiple commands run during this installation process.
        """
        if not self.class_members:
            self.module.fail_json(msg="Empty class cannot be created.")

        rc = None
        out = ''
        err = ''

        if self.exists() and not self.class_check_cups_options():
            (rc, uninstall_out, uninstall_err) = self._cups_object_uninstall()

            out = (out + '\n' + uninstall_out).strip('\n')
            err = (err + '\n' + uninstall_err).strip('\n')

        if not self.exists():
            (rc, install_out, install_err) = self._class_install()

            out = (out + '\n' + install_out).strip('\n')
            err = (err + '\n' + install_err).strip('\n')

        if self.exists():
            self._class_install_mandatory_options()

        return rc, out, err


# ===========================================


def main():
    """
    main function that populates this ansible module with variables and sets it in motion.

    First and Ansible Module is defined with the variable definitions and default values.
    Then a CUPSObject is created using using this module. CUPSObject populates its own values based on the module vars.

    Based on state, the following is done:
    - state=present:
        - printer_or_class=printer:
            - Call CUPSObject.printer_install() to install the printer.
        - printer_or_class=class:
            - Call CUPSObject.class_install() to install the class.
    - state=absent:
        - Call CUPSObject.cups_object_uninstall() to uninstall either a printer or a class.

    Records the rc, out, err values of the commands run above and accordingly exists the module and sends the status
    back to to Ansible using module.exit_json().
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            driver=dict(required=False, default='model', choices=['model', 'ppd'], type='str'),
            purge=dict(required=False, default=False, type='bool'),
            name=dict(required=False, type='str'),
            printer_or_class=dict(default='printer', required=False, type='str', choices=['printer', 'class']),
            uri=dict(required=False, default=None, type='str'),
            enabled=dict(required=False, default=True, type='bool'),
            shared=dict(required=False, default=False, type='bool'),
            default=dict(required=False, default=False, type='bool'),
            model=dict(required=False, default=None, type='str'),
            info=dict(required=False, default=None, type='str'),
            location=dict(required=False, default=None, type='str'),
            assign_cups_policy=dict(required=False, default=None, type='str'),
            class_members=dict(required=False, default=[], type='list'),
            report_ipp_supply_levels=dict(required=False, default=True, type='bool'),
            report_snmp_supply_levels=dict(required=False, default=True, type='bool'),
            job_kb_limit=dict(required=False, default=None, type='int'),
            job_quota_limit=dict(required=False, default=None, type='int'),
            job_page_limit=dict(required=False, default=None, type='int'),
            options=dict(required=False, default={}, type='dict'),
        ),
        required_one_of = [['name', 'purge']],
        supports_check_mode=True
    )

    cups_object = CUPSObject(module)

    rc = None
    out = ''
    err = ''

    result = {'state': module.params['state'],
              'purge': module.params['purge'],
              'printer_or_class': module.params['printer_or_class'],
              'name': cups_object.name}

    # Check purge option and purge all printers if exists
    if result['purge'] and not module.check_mode:
        (rc, out, err) = cups_object.cups_object_purge()
        if not result['name']:
            module.exit_json(changed=True, msg="All printers purged")

    # Checking if printer or class AND if state is present or absent and calling the appropriate method.
    if result['state'] == 'present':
        if result['printer_or_class'] == 'printer':
            (rc, out, err) = cups_object.printer_install()
        elif result['printer_or_class'] == 'class':
            (rc, out, err) = cups_object.class_install()
    elif result['state'] == 'absent':
        (rc, out, err) = cups_object.cups_object_uninstall()

    result['changed'] = False if rc is None else True

    if out:
        result['stdout'] = out

    if err:
        result['stderr'] = err

    module.exit_json(**result)

# Import statements at the bottom as per Ansible best practices.
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
