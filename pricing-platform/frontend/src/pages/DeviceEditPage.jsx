import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import DeviceForm from "../features/devices/DeviceForm";
import { useDevice, useUpdateDevice } from "../features/devices/hooks";

export default function DeviceEditPage() {
  const { deviceId } = useParams();
  const navigate = useNavigate();
  const { data: device, isLoading, isError } = useDevice(deviceId);
  const updateDevice = useUpdateDevice(deviceId);

  const handleSubmit = async (payload) => {
    await updateDevice.mutateAsync(payload);
    navigate(`/devices/${deviceId}`, { replace: true });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !device) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Device not found.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit Device
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <DeviceForm defaultValues={device} onSubmit={handleSubmit} submitLabel="Save Changes" />
      </Paper>
    </Container>
  );
}
