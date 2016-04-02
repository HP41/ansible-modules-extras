#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, David Symons (Multimac) <Mult1m4c@gmail.com>
# (c) 2016, Konstantin Shalygin <k0ste@cn.ru>
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
short_description: Manages printers in CUPS via lpadmin
description:
    - Creates, removes and sets options for printers in CUPS.
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
    options:
        description:
            - A dictionary of key-value pairs describing printer options and their required value.
        default: { }
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
    options:
      media: 'iso_a4_210x297mm'

# Creates a Zebra ZPL printer called zebra
- cups_lpadmin: state=present name=zebra uri=192.168.1.2 model=drv:///sample.drv/zebra.ppd

# Updates the zebra printer with some custom options
- cups_lpadmin:
    state: present
    name: zebra
    uri: 192.168.1.2
    model: drv:///sample.drv/zebra.ppd
    options:
      PageSize: w288h432

# Creates a raw printer called raw_test
- cups_lpadmin: state=present name=raw_test uri=192.168.1.3

# Deletes the printers set up by the previous tasks
- cups_lpadmin: state=absent name=zebra
- cups_lpadmin: state=absent name=raw_test
'''

class CUPSPrinter(object):

    def __init__(self, module):
        self.module = module

        self.driver = module.params['driver']
        self.name = module.params['name']
        self.uri = module.params['uri']

        self.enabled = module.params['enabled']
        self.shared = module.params['shared']
        self.default = module.params['default']

        self.model = module.params['model']

        self.info = module.params['info']
        self.location = module.params['location']

        self.options = module.params['options']

        # Use lpd if a protocol is not specified
        if self.uri and ':/' not in self.uri:
            self.uri = 'lpd://{0}/'.format(self.uri)

    def _get_installed_drivers(self):
        cmd = ['lpinfo', '-l', '-m']
        (rc, out, err) = self.module.run_command(cmd)

        # We want to split on sections starting with "Model:" as that specifies
        # a new available driver
        prog = re.compile("^Model:", re.MULTILINE)
        cups_drivers = re.split(prog, out)

        drivers = { }
        for d in cups_drivers:

            # Skip if the line contains only whitespace
            if not d.strip():
                continue

            curr = { }
            for l in d.splitlines():
                kv = l.split('=', 1)

                # Strip out any excess whitespace from the key/value
                kv = map(str.strip, kv)

                curr[kv[0]] = kv[1]

            # If no protocol is specified, then it must be on the local filesystem
            # By default there is no preceeding '/' on the path, so it must be prepended
            if not '://' in curr['name']:
                curr['name'] = '/{0}'.format(curr['name'])

            # Store drivers by their 'name' (i.e. path to driver file)
            drivers[curr['name']] = curr

        return drivers

    def _get_make_and_model(self):
        if not self.driver or self.driver == 'model':
            '''Raw printer is defined or model not defined'''
            if not self.model or self.model == 'raw':
                return "Local Raw Printer"
        elif self.driver == 'ppd':
            return

        installed_drivers = self._get_installed_drivers()
        if self.model in installed_drivers:
            return installed_drivers[self.model]['make-and-model']

        self.module.fail_json(msg="unable to determine printer make and model")

    def _install_printer(self):
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

    def _install_printer_options(self):
        cmd = ['lpadmin', '-p', self.name]

        for k, v in self.options.iteritems():
            cmd.extend(['-o', '{0}={1}'.format(k, v)])

        '''Target printer is default server printer'''
        if self.default:
            cmd.extend(['-d', self.name])

        return self.module.run_command(cmd)

    def _uninstall_printer(self):
        cmd = ['lpadmin', '-x', self.name]
        return self.module.run_command(cmd)

    def get_printer_cups_options(self):
        '''Returns the CUPS options for the printer'''
        cmd = ['lpoptions', '-p', self.name]
        (rc, out, err) = self.module.run_command(cmd)

        options = { }
        for s in shlex.split(out):
            kv = s.split('=', 1)

            if len(kv) == 1: # If we only have an option name, set it's value to None
                options[kv[0]] = None
            elif len(kv) == 2: # Otherwise set it's value to what we received
                options[kv[0]] = kv[1]

        return options

    def get_printer_specific_options(self):
        '''Returns the printer specific options for the printer, as well as the accepted options'''
        cmd = ['lpoptions', '-p', self.name, '-l']
        (rc, out, err) = self.module.run_command(cmd)

        options = { }
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

                v = v[1:] # Strip the '*' from the value

                current_value = v
                break

            options[name] = {
                'current': current_value,
                'label': label,
                'values': values,
            }

        return options

    def check_cups_options(self):
        expected_cups_options = {
            'device-uri': self.uri,
            'printer-make-and-model': self._get_make_and_model(),

            'printer-location': self.location,
        }

        # 'printer-info' defaults to the printer name if not specified manually
        if self.info:
            expected_cups_options['printer-info'] = self.info
        else:
            expected_cups_options['printer-info'] = self.name

        if self.shared:
            expected_cups_options['printer-is-shared'] = 'true'
        else:
            expected_cups_options['printer-is-shared'] = 'false'

        cups_options = self.get_printer_cups_options()
        for k in expected_cups_options:
            if k not in cups_options:
                return False

            if expected_cups_options[k] != cups_options[k]:
                return False

        return True

    def check_printer_options(self):
        expected_printer_options = self.options

        printer_options = self.get_printer_specific_options()
        for k in expected_printer_options:
            if k not in printer_options:
                return False

            if expected_printer_options[k] != printer_options[k]['current']:
                return False

        return True

    def exists(self):
        cmd = ['lpstat', '-p', self.name]
        (rc, out, err) = self.module.run_command(cmd)

        # This command will fail if the self.name doesn't exist (rc != 0)
        return rc == 0

    def install(self):
        if self.uri is None:
            self.module.fail_json(msg="'uri' is required for present state")

        rc = None
        out = ''
        err = ''

        if self.exists() and not self.check_cups_options():
            (rc, uninstall_out, uninstall_err) = self._uninstall_printer()

            out = (out + '\n' + uninstall_out).strip('\n')
            err = (err + '\n' + uninstall_err).strip('\n')

        if not self.exists():
            (rc, install_out, install_err) = self._install_printer()

            out = (out + '\n' + install_out).strip('\n')
            err = (err + '\n' + install_err).strip('\n')

        if not self.check_printer_options():
            (rc, options_out, options_err) = self._install_printer_options()

            out = (out + '\n' + options_out).strip('\n')
            err = (err + '\n' + options_err).strip('\n')

        return (rc, out, err)

    def uninstall(self):
        rc = None
        out = ''
        err = ''

        if self.exists():
            (rc, out, err) = self._uninstall_printer()

        return (rc, out, err)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['present', 'absent'], type='str'),
            driver = dict(default='model', choices=['model', 'ppd'], type='str'),
            name = dict(required=True, type='str'),
            uri = dict(default=None, type='str'),
            enabled = dict(default=True, type='bool'),
            shared = dict(default=False, type='bool'),
            default = dict(default=False, type='bool'),
            model = dict(default=None, type='str'),
            info = dict(default=None, type='str'),
            location = dict(default=None, type='str'),
            options = dict(default={ }, type='dict'),
        ),
        supports_check_mode=False
    )

    cups_printer = CUPSPrinter(module)

    rc = None
    out = ''
    err = ''

    result = { }
    result['state'] = module.params['state']
    result['name'] = cups_printer.name

    state = module.params['state']
    if state == 'present':
        (rc, out, err) = cups_printer.install()
    elif state == 'absent':
        (rc, out, err) = cups_printer.uninstall()

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True

    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
