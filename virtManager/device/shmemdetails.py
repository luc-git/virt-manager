from virtinst import DeviceShMem

from ..lib import uiutil
from ..baseclass import vmmGObjectUI

_EDIT_SHMEM_ENUM = range(1, 10)
(
    _EDIT_SHMEM_TYPE,
    _EDIT_SHMEM_NAME,
    _EDIT_SHMEM_SIZE,
    _EDIT_SHMEM_PATH,
    _EDIT_SHMEM_MODEL,
    _EDIT_SHMEM_ROLE,
    _EDIT_SHMEM_MSI,
    _EDIT_SHMEM_MSI_ENABLE,
    _EDIT_SHMEM_MSI_IO,
) = _EDIT_SHMEM_ENUM


class vmmShmemDetails(vmmGObjectUI):
    __gsignals__ = {
        "changed": (vmmGObjectUI.RUN_FIRST, None, []),
    }

    def __init__(self, vm, builder, topwin):
        super().__init__("shmem.ui", None, builder=builder, topwin=topwin)
        self.vm = vm
        self.conn = vm.conn

        self._active_edits = []

        def _e(edittype):
            def signal_cb(*args):
                self._change_cb(edittype)

            return signal_cb

        self.builder.connect_signals({
            "on_shmem_name_changed": _e(_EDIT_SHMEM_NAME),
            "on_shmem_size_changed": _e(_EDIT_SHMEM_SIZE),
            "on_shmem_path_changed": _e(_EDIT_SHMEM_PATH),
            "on_shmem_model_changed": _e(_EDIT_SHMEM_MODEL),
            "on_shmem_role_changed": _e(_EDIT_SHMEM_ROLE),
            "on_shmem_msi_enabled": _e(_EDIT_SHMEM_MSI_ENABLE),
            "on_shmem_msi_value_changed": _e(_EDIT_SHMEM_MSI),
            "on_shmem_io_enabled": _e(_EDIT_SHMEM_MSI_IO)
        })

        self._init_ui()
        self.top_box = self.widget("top-box")

    def _cleanup(self):
        self.vm = None
        self.conn = None

    ##############
    # UI helpers #
    ##############

    def _init_ui(self):

        rows = [
            # [DeviceShMem.MODEL_IVSHMEM, _("IVSHMEM")],
            [DeviceShMem.MODEL_IVSHMEM_PLAIN, _("IVSHMEM PLAIN")],
            [DeviceShMem.MODEL_IVSHMEM_DOORBELL, _("IVSHMEM DOORBELL")],
        ]
        uiutil.build_simple_combo(self.widget("shmem-model"), rows, sort=False)

        rows = [
            [DeviceShMem.ROLE_MASTER, _("ROLE_MASTER")],
            [DeviceShMem.ROLE_PEER, _("ROLE_PEER")],
            [None, "None"]
        ]
        uiutil.build_simple_combo(self.widget("shmem-role"), rows, sort=False)

        rows = []
        d = {}
        for i in (2 ** p for p in range(0, 20)):
            d["SIZE_{0}".format(i)] = i
            rows.append([d["SIZE_{0}".format(i)], _(str(i))])

        uiutil.build_simple_combo(self.widget("shmem-size"), rows, sort=False)

        uiutil.set_grid_row_visible(self.widget("shmem-name"), visible=True)

    def _sync_ui(self):
        devtype = uiutil.get_list_selection(self.widget("shmem-model"))

        uiutil.set_grid_row_visible(self.widget("shmem-path"), devtype == DeviceShMem.MODEL_IVSHMEM_DOORBELL)
        uiutil.set_grid_row_visible(self.widget("shmem-msi"), devtype == DeviceShMem.MODEL_IVSHMEM_DOORBELL)
        uiutil.set_grid_row_visible(self.widget("shmem-size"), devtype == DeviceShMem.MODEL_IVSHMEM_PLAIN)
        uiutil.set_grid_row_visible(self.widget("msi-io"), devtype == DeviceShMem.MODEL_IVSHMEM_DOORBELL)
        uiutil.set_grid_row_visible(self.widget("shmem-size"), devtype == DeviceShMem.MODEL_IVSHMEM_PLAIN)
        self.widget("shmem-msi").set_sensitive(self.widget("msi-enable").get_active())

    def reset_state(self):
        self.widget("shmem-name").set_text("ivshmem_0")
        uiutil.set_list_selection(self.widget("shmem-role"), None)
        uiutil.set_list_selection(self.widget("shmem-model"), DeviceShMem.MODEL_IVSHMEM_PLAIN)

    def set_dev(self, dev):
        self.reset_state()

        self.widget("shmem-msi").set_value(dev.msi_vectors or 0)

        uiutil.set_list_selection(self.widget("shmem-size"), dev.size)

        uiutil.set_list_selection(self.widget("shmem-model"), dev.type)

        uiutil.set_list_selection(self.widget("shmem-role"), dev.role)

        self.widget("shmem-name").set_text(dev.name)

        self.widget("shmem-path").set_text(dev.server_path or "")
        self.widget("msi-io").set_active(dev.msi_ioeventfd)

        self._active_edits = []

    def _set_values(self, dev):
        name = self.widget("shmem-name").get_text()
        path = self.widget("shmem-path").get_text()
        model = uiutil.get_list_selection(self.widget("shmem-model"))
        role = uiutil.get_list_selection(self.widget("shmem-role"))
        msi = uiutil.spin_get_helper(self.widget("shmem-msi"))
        msi_io = self.widget("msi-io").get_active()
        size = uiutil.get_list_selection(self.widget("shmem-size"))

        if model == 'ivshmem-plain':
            path = None
            msi_io = None
            msi = None
            dev.server_path = None
            dev.msi_ioeventfd = None
            dev.msi_vectors = None
        elif not self.widget("msi-enable").get_active():
            msi = None
            dev.msi_vectors = None

        if model == 'ivshmem-doorbell':
            dev.size = None
            size = None

        if _EDIT_SHMEM_NAME in self._active_edits:
            dev.name = name
        if _EDIT_SHMEM_ROLE in self._active_edits:
            dev.role = role
        if _EDIT_SHMEM_MODEL in self._active_edits:
            dev.type = model
        if _EDIT_SHMEM_PATH in self._active_edits:
            dev.server_path = path
        if _EDIT_SHMEM_MSI in self._active_edits:
            dev.msi_vectors = msi
        if _EDIT_SHMEM_MSI_IO in self._active_edits:
            dev.msi_ioeventfd = msi_io
        if _EDIT_SHMEM_SIZE in self._active_edits:
            dev.size = size
        dev.size_unit = "M"

        return dev

    def build_device(self):
        self._active_edits = _EDIT_SHMEM_ENUM[:]

        conn = self.conn.get_backend()
        dev = DeviceShMem(conn)
        self._set_values(dev)

        dev.validate()
        return dev

    def update_device(self, dev):
        newdev = DeviceShMem(dev.conn, parsexml=dev.get_xml())
        self._set_values(newdev)
        return newdev

    #############
    # Listeners #
    #############

    def _change_cb(self, edittype):
        self._sync_ui()
        if edittype not in self._active_edits:
            self._active_edits.append(edittype)
        self.emit("changed")
