import urwid

import callback
import util
import widgets.frames as frames
import widgets.inputs as inputs

ENCRYPTED_SCHEMA = [
    ("1", 1, "vfat", "/boot/efi"),
    ("2", 2, "ext4", "/boot")
]

UNENCRYPTED_SCHEMA = [
    ("1", 1, "vfat", "/boot/efi")
]

class DeployScreen:
    def __init__(self, controller):
        self.controller = controller
        title_text = "Deploy System"
        self.ready = False
        self.flag_encrypt = True # Allows us to set the default value; default True to encrypt devices with TPM

        self.tpm_text=""
        self.tpm_conf_text=""

        # Left column: basic details
        disks = []
        for disk in util.get_disks():
            disks.append(f"{disk.get('device')} ({disk.get('capacity')}) [{disk.get('model')}]")

        disks[0] = (disks[0], self.flag_encrypt)
        self.disk_toggles = inputs.Togglegroup(disks)

        os_list = []
        for os in util.get_data("images"):
            if os.get("default"):
                os_list.append((os.get("display"), os.get("default")))
            else:
                os_list.append(os.get("display"))
        self.version_toggles = inputs.Togglegroup(os_list) 
        self.hostname_field = urwid.AttrMap(urwid.Edit(wrap='clip'), 'edit-regular', 'edit-highlight')

        # TPM fields
        self.tpm_alert_field = urwid.Text("", align='right')
        self.tpm_conf_alert_field = urwid.Text("", align='right')

        self.tpm_psk_edit = urwid.Edit(mask='*', wrap='clip')
        self.tpm_psk_confirm_edit = urwid.Edit(mask='*', wrap='clip')

        self.tpm_psk_field = urwid.AttrMap(self.tpm_psk_edit, 'edit-regular', 'edit-highlight')
        self.tpm_psk_field_confirm = urwid.AttrMap(self.tpm_psk_confirm_edit, 'edit-regular', 'edit-highlight')

        # Connect TPM field signals
        urwid.connect_signal(self.tpm_psk_edit, 'change', self.luks_pk_change_callback)
        urwid.connect_signal(self.tpm_psk_confirm_edit, 'change', self.luks_pk_conf_change_callback)

        self.encryption_box_toggle = inputs.CheckRadioBox("Encrypt Device", state=True)
        urwid.connect_signal(self.encryption_box_toggle, 'post_change', self.luks_enable_box_callback)
        encryption_box_contents = [
            self.encryption_box_toggle,
            urwid.Divider(),
            urwid.Columns([urwid.Text("LUKS Passphrase"), urwid.AttrMap(self.tpm_alert_field, 'text-error')]),
            self.tpm_psk_field,
            urwid.Columns([urwid.Text("Confirm LUKS Passphrase"), urwid.AttrMap(self.tpm_conf_alert_field, 'text-error')]),
            self.tpm_psk_field_confirm,
        ]
        encryption_box_pile = urwid.Pile(encryption_box_contents)
        encryption_box = frames.RoundedLineBox(encryption_box_pile, "Encryption Settings")

        left_col_contents = [
            urwid.Text("Target Disk"),
            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            self.disk_toggles,

            urwid.Divider(),

            urwid.Text("Operating System"),
            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            self.version_toggles,
            
            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            urwid.Text("Hostname"),
            self.hostname_field,
            
            urwid.Divider(),
            
            encryption_box
        ]
        left_col = urwid.Pile(left_col_contents)

        # Middle column: extra features
        packages_list = []
        for package in util.get_data("available_packages"):
            if package.get("default"):
                packages_list.append((package.get("display"), package.get("default")))
            else:
                packages_list.append(package.get("display"))
        self.packages_checkboxes = inputs.Togglegroup(packages_list, True)

        # TODO: filesystems
        self.root_partition_fstypes = inputs.Togglegroup([('ext4', True), 'btrfs'])

        extra_options_list = []
        for option in util.get_data("options"):
            if option.get("default"):
                extra_options_list.append((option.get("display"), option.get("default")))
            else:
                extra_options_list.append(option.get("display"))

        self.extra_features = inputs.Togglegroup(extra_options_list, True)

        # Create column objects
        mid_col_contents = [
            urwid.Text("Extra Packages"),
            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            self.packages_checkboxes,

            urwid.Divider(),
            
            urwid.Text("Root partition filesystem"),
            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            self.root_partition_fstypes,

            urwid.Divider(),

            urwid.Text("Additional options"),
            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            self.extra_features,

        ]
        mid_col = urwid.Pile(mid_col_contents)

        # Right column: Extra partitioning and confirmation

        self.overview_pile = urwid.AttrMap(urwid.Text("Loading..."), 'text-warning')

        right_col_contents = [
            urwid.Text("Deployment Overview"),
            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            
            self.overview_pile,

            urwid.Divider(util.LINE_SINGLE_HORIZONTAL),
            urwid.Button("Begin Deployment", on_press=self.submit_button_callback),
            urwid.Button("Main Menu", on_press=self.cancel_button_callback, user_data="scr:main")
        ]
        right_col = urwid.Pile(right_col_contents)

        # Layout and frame
        layout = urwid.Columns([left_col, mid_col, right_col], dividechars=1)
        box = frames.DoubleLineBox(layout, title_text)

        self.root = box # Set root component returned by `render()`

    def render(self):
        return self.root

    def button_callback(self, button, data):
        callback.callback(self.controller, data)

    def hostname_change_callback(self, edit, text):
        self.controller.set_variable("hostname", text.lowercase()) # Ensure the hostname is all lowercase; TODO: validate

    def luks_pk_change_callback(self, edit, text):
        self.tpm_text = text
        self.update_alerts()

    def luks_pk_conf_change_callback(self, edit, text):
        self.tpm_conf_text = text
        self.update_alerts()
    
    def luks_enable_box_callback(self, checkbox, new_state):
        self.flag_encrypt = checkbox.state
        if not checkbox.state:
            self.tpm_psk_field = urwid.AttrMap(urwid.Text(self.tpm_psk_edit.get_text()[0]), "edit-disabled")
            self.tpm_psk_field_confirm = urwid.AttrMap(urwid.Text(self.tpm_psk_confirm_edit.get_text()[0]), "edit-disabled")

            self.tpm_alert_field.set_text("")
            self.tpm_conf_alert_field.set_text("")
        else:
            self.tpm_psk_field = urwid.AttrMap(self.tpm_psk_edit, "edit-regular")
            self.tpm_psk_field_confirm = urwid.AttrMap(self.tpm_psk_confirm_edit, "edit-regular")

            self.update_alerts()
    
    def submit_button_callback(self, button):
        popup_contents = [
            urwid.Text("This process is IRREVERSABLE!!!"),
            urwid.Divider(),
            urwid.Text("Press 'Begin' to start the deployment.")
        ]

        # Set controller's variables for version, extras, disk, etc.
        self.controller.set_variable("os_version", self.version_toggles.get_selected())
        self.controller.set_variable("target_disk", self.disk_toggles.get_selected())
        self.controller.set_variable("do_encrypt", self.flag_encrypt)
        self.controller.set_variable("install_pkgs", self.packages_checkboxes.get_selected())
        self.controller.set_variable("root_fstype", self.root_partition_fstypes.get_selected())
        self.controller.set_variable("extra_options", self.extra_features.get_selected())

        popup_pile = urwid.Pile(popup_contents)
        self.controller.popup("Confirm begin?", popup_pile, action=['popup:Begin:deploy', 'popup:Cancel:hide'], attribute='popup-warning')

    def cancel_button_callback(self, button, data):
        callback.callback(self.controller, data)

    def update_overview(self):
        for disks in util.get_disks():
            pass

        pass

    def update_alerts(self):

        if self.flag_encrypt:
            if len(self.tpm_text) < 10:
                self.tpm_alert_field.set_text("Must be longer than 10 characters")
                self.ready = False
                return

            if self.tpm_text != self.tpm_conf_text:
                self.tpm_conf_alert_field.set_text("Passwords do not match")
                self.tpm_alert_field.set_text("Passwords do not match")
                self.ready = False
                return

        self.ready = True
        self.tpm_conf_alert_field.set_text("")
        self.tpm_alert_field.set_text("")
        pass
