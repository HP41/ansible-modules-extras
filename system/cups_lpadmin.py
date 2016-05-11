#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, David Symons (Multimac) <Mult1m4c@gmail.com>
# (c) 2016, Konstantin Shalygin <k0ste@cn.ru>
# (c) 2016, Hitesh Prabhakar <hiteshprab@gmail.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cups_lpadmin
author:
    - "David Symons (Multimac) <Mult1m4c@gmail.com>"
    - "Konstantin Shalygin <k0ste@cn.ru>"
    - "Hitesh Prabhakar <hiteshprab@gmail.com>"
short_description: Manages printers in CUPS via lpadmin
description:
    - Creates, removes and sets options for printers in CUPS.
    - Creates, removes and sets options for classes in CUPS.
    - For classes the members are defined as a final state and therefore will only have the members defined.
version_added: "2.1"
notes: []
requirements:
    - CUPS 1.7+
options:
    name:
        description:
            - Name of the printer in CUPS
        required: true
        default: null
    state:
        description:
            - Whether the printer should or not be in CUPS.
        required: false
        default: present
        choices: ["present", "absent"]
    printer_or_class:
        description: State whether the object we are working on is a printer or class
        required: true
        default: null
        choices: ['printer', 'class']
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
            - A list of printers to be added to this class
        required: false
        default: null
        type: list
    report_ipp_supply_levels:
        description:
            - Whether or not the printer must report supply status via IPP
        required: false
        default: true
        choices: ["true", "false"]
    report_snmp_supply_levels:
        description:
            - Whether or not the printer must report supply status via SNMP (RFC 3805)
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

EXAMPLES = '''
# Creates HP printer via ethernet, set default paper size and
  make this printer as server default
- cups_lpadmin:
    name: 'HP_M1536'
    state: 'present'
    uri: 'hp:/net/HP_LaserJet_M1536dnf_MFP?ip=192.168.1.2'
    model: 'drv:///hp/hpcups.drv/hp-laserjet_m1539dnf_mfp-pcl3.ppd'
    default: 'true'
    location: 'Lib'
    info: 'MFP'
    printer_assign_policy: 'students'
    report_ipp_supply_levels: 'true'
    report_snmp_supply_levels: 'false'
    # belongs_to_class: 'Lab Printers'
    options:
      media: 'iso_a4_210x297mm'

# Create CUPS Class
- cups_lpadmin:
    state: present
    printer_or_class: class
    class_members: "{{a_yaml_array}}"
    info: 'A test class'
    location: 'A place of great importance'

# Creates a Zebra ZPL printer called zebra
- cups_lpadmin: state=present name=zebra uri=192.168.1.2 model=drv:///sample.drv/zebra.ppd

# Updates the zebra printer with some custom options
- cups_lpadmin:
    state: present
    name: zebra
    uri: 192.168.1.2
    model: drv:///sample.drv/zebra.ppd
    job_kb_limit: 2048
    job_quota_limit: 86400
    job_page_limit: 10
    # belongs_to_class: Accounting Printers
    # present_in_class: false
    options:
      PageSize: w288h432

# Creates a raw printer called raw_test
- cups_lpadmin: state=present name=raw_test uri=192.168.1.3

# Deletes the printers set up by the previous tasks
- cups_lpadmin: state=absent name=zebra
- cups_lpadmin: state=absent name=raw_test
'''


class CUPSObject(object):
    # Methods starting with 'cups_object' can be used with both printer and classes.
    # Methods starting with 'class' are meant to work with classes only.
    # Methods starting with 'printer' are meant to work with printers only.

    # Class Members defined in this script will be the final list of printers in that class.
    # It cannot add or remove from an existing list that might have more members that defined.
    # It'll uninstall the class and create it from scratch as defined in this script if the defined member list
    # and the actual member list don't match.

    def __init__(self, module):
        self.module = module

        self.driver = module.params['driver']
        self.name = module.params['name']

        self.uri = module.params['uri']
        # Use lpd if a protocol is not specified
        if self.uri and ':/' not in self.uri:
            self.uri = 'lpd://{0}/'.format(self.uri)

        self.enabled = module.params['enabled']
        self.shared = module.params['shared']
        self.default = module.params['default']

        self.model = module.params['model']

        self.info = module.params['info']
        self.location = module.params['location']

        self.options = module.params['options']

        self.assign_cups_policy = module.params['assign_cups_policy']

        self.class_members = module.params['class_members']

        self.report_ipp_supply_levels = module.params['report_ipp_supply_levels']
        self.report_snmp_supply_levels = module.params['report_snmp_supply_levels']
        self.job_kb_limit = module.params['job_kb_limit']
        self.job_quota_limit = module.params['job_quota_limit']
        self.job_page_limit = module.params['job_page_limit']

    def _printer_get_installed_drivers(self):
        cmd = ['lpinfo', '-l', '-m']
        (rc, out, err) = self.module.run_command(cmd)

        # We want to split on sections starting with "Model:" as that specifies
        # a new available driver
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

            # If no protocol is specified, then it must be on the local filesystem
            # By default there is no preceding '/' on the path, so it must be prepended
            if '://' not in curr['name']:
                curr['name'] = '/{0}'.format(curr['name'])

            # Store drivers by their 'name' (i.e. path to driver file)
            drivers[curr['name']] = curr

        return drivers

    def _printer_get_make_and_model(self):
        if self.driver == 'model':
            # Raw printer is defined
            if not self.model or self.model == 'raw':
                return "Local Raw Printer"
        elif self.driver == 'ppd':
            return

        installed_drivers = self._printer_get_installed_drivers()
        if self.model in installed_drivers:
            return installed_drivers[self.model]['make-and-model']

        self.module.fail_json(msg="unable to determine printer make and model")

    def _printer_install(self):
        cmd = ['lpadmin', '-p', self.name, '-v', self.uri]

        if self.enabled:
            cmd.append('-E')

        if self.shared:
            cmd.extend(['-o', 'printer-is-shared=true'])
        else:
            cmd.extend(['-o', 'printer-is-shared=false'])

        if self.driver == 'model':
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

    # cupsIPPSupplies, cupsSNMPSupplies, job-k-limit, job-page-limit, printer-op-policy,
    # job-quota-period cannot be checked via cups command-line tools yet.
    # Therefore force set these options if they exist
    def _printer_install_uncheckable_options(self):
        cmd = ['lpadmin', '-p', self.name]

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

        return self.module.run_command(cmd)

    def _printer_install_options(self):
        cmd = ['lpadmin', '-p', self.name]

        for k, v in self.options.iteritems():
            cmd.extend(['-o', '{0}={1}'.format(k, v)])

        if self.default:
            cmd.extend(['-d', self.name])

        return self.module.run_command(cmd)

    def _class_install(self):
        rc = None
        out = ''
        err = ''
        for printer in self.class_members:
            # Going through all the printers that are supposed to be in the class and adding them to said class.
            # Ensuring first the printer exists.
            if self.exists(another_object_to_check=printer):
                (rc, install_out, install_err) = self.module.run_command(['lpadmin', '-p', printer, '-c', self.name])
                out = (out + '\n' + install_out).strip('\n')
                err = (err + '\n' + install_err).strip('\n')
            else:
                self.module.fail_json(msg="Printer {0} for class {1} doesn't exist".format(printer, self.name))

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

    # cupsIPPSupplies, cupsSNMPSupplies, printer-op-policy, cannot be checked via cups command-line tools yet.
    # Therefore force set these options if they exist
    def _class_install_uncheckable_options(self):
        orig_cmd = ['lpadmin', '-p', self.name]
        cmd = list(orig_cmd)  # Making a copy of the list/array

        rc = None
        out = ''
        err = ''

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
            out = out.strip('\n')
            err = err.strip('\n')

        return rc, out, err

    # Common method to uninstall a CUPS Object - Printer or Class
    def _cups_object_uninstall(self):
        cmd = ['lpadmin', '-x', self.name]
        return self.module.run_command(cmd)

    # Has an optional 'another_object_to_be_checked' argument that can be sent to check
    # if that object (printer or class) exists instead.
    def exists(self, another_object_to_check=None):
        cmd = ['lpstat', '-p']

        if another_object_to_check is None:
            cmd.append(self.name)
        else:
            cmd.append(another_object_to_check)

        (rc, out, err) = self.module.run_command(cmd)
        return rc == 0

    # Returns the CUPS options for the printer
    def cups_object_get_cups_options(self):
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

    # Checks defined/expected CUPS options for said printer against current CUPS options and returns a boolean.
    def printer_check_cups_options(self):
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

    # Returns the class members of a class
    def class_get_current_members(self):
        cmd = ['lpstat', '-c', self.name]
        (rc, out, err) = self.module.run_command(cmd)

        if err:
            self.module.fail_json(
                msg="Error occured while trying to 'lpstat' class - {0} - {1}".format(self.name, err))

        members = []
        temp = shlex.split(out)
        # Skip first line as it's an information line.
        temp = temp[1:]
        for m in temp:
            str.strip(m)
            members.append(m)

        return members

    # Returns the printer specific options for the printer, as well as the accepted options
    def printer_get_specific_options(self):
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
        expected_printer_options = self.options

        printer_options = self.printer_get_specific_options()
        for k in expected_printer_options:
            if k not in printer_options:
                return False

            if expected_printer_options[k] != printer_options[k]['current']:
                return False

        return True

    def printer_install(self):
        if self.uri is None:
            self.module.fail_json(msg="'uri' is required for present state")

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
            (rc, uncheckable_out, uncheckable_err) = self._printer_install_uncheckable_options()

            out = (out + '\n' + uncheckable_out).strip('\n')
            err = (err + '\n' + uncheckable_err).strip('\n')

        if not self.printer_check_options():
            (rc, options_out, options_err) = self._printer_install_options()

            out = (out + '\n' + options_out).strip('\n')
            err = (err + '\n' + options_err).strip('\n')

        return rc, out, err

    # Can uninstall both a printer and class
    def cups_object_uninstall(self):
        rc = None
        out = ''
        err = ''

        if self.exists():
            (rc, out, err) = self._cups_object_uninstall()

        return rc, out, err

    # cupsIPPSupplies, cupsSNMPSupplies, printer-op-policy, cannot be checked via cups command-line tools yet.
    # Therefore force set these options if they exist
    def class_install(self):
        if self.class_members is None:
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
            (rc, uncheckable_out, uncheckable_err) = self._class_install_uncheckable_options()

            out = (out + '\n' + uncheckable_out).strip('\n')
            err = (err + '\n' + uncheckable_err).strip('\n')

        return rc, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            driver=dict(default='model', choices=['model', 'ppd'], type='str'),
            name=dict(required=True, type='str'),
            printer_or_class=dict(required=True, type='str', choices=['printer', 'class']),
            uri=dict(default=None, type='str'),
            enabled=dict(default=True, type='bool'),
            shared=dict(default=False, type='bool'),
            default=dict(default=False, type='bool'),
            model=dict(default=None, type='str'),
            info=dict(default=None, type='str'),
            location=dict(default=None, type='str'),
            assign_cups_policy=dict(default=None, type='str'),
            class_members=dict(default=[], type='list'),
            report_ipp_supply_levels=dict(default=True, type='bool'),
            report_snmp_supply_levels=dict(default=True, type='bool'),
            job_kb_limit=dict(default=None, type='int'),
            job_quota_limit=dict(default=None, type='int'),
            job_page_limit=dict(default=None, type='int'),
            options=dict(default={}, type='dict'),
        ),
        supports_check_mode=False
    )

    cups_object = CUPSObject(module)

    rc = None
    out = ''
    err = ''

    result = {'state': module.params['state'],
              'printer_or_class': module.params['printer_or_class'],
              'name': cups_object.name}

    # Checking if printer or class AND if state is present or absent and calling the appropriate method.

    if result['printer_or_class'] == 'printer':
        if result['state'] == 'present':
            (rc, out, err) = cups_object.printer_install()
        elif result['state'] == 'absent':
            (rc, out, err) = cups_object.cups_object_uninstall()
    elif result['printer_or_class'] == 'class':
        if result['state'] == 'present':
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