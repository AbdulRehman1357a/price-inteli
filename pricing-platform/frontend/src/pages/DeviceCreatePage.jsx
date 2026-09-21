import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import DeviceForm from "../features/devices/DeviceForm";
import { useCreateDevice } from "../features/devices/hooks";

export default function DeviceCreatePage() {
  const navigate = useNavigate();
  const createDevice = useCreateDevice();

  const handleSubmit = async (payload) => {
    const device = await createDevice.mutateAsync(payload);
    navigate(`/devices/${device.id}`, { replace: true });
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Device
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <DeviceForm onSubmit={handleSubmit} submitLabel="Register Device" isCreate />
      </Paper>
    </Container>
  );
}
