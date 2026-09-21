import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { useNavigate } from "react-router-dom";

import DeviceManagementTabs from "./DeviceManagementTabs";

export default function DeviceManageDialog({ device, onClose }) {
  const navigate = useNavigate();

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{device.device_name}</DialogTitle>
      <DialogContent>
        <DeviceManagementTabs deviceId={device.id} />
      </DialogContent>
      <DialogActions>
        <Button onClick={() => navigate(`/devices/${device.id}`)}>Open full page</Button>
        <Button variant="contained" onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
