import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import DeviceManagementTabs from "../features/devices/DeviceManagementTabs";
import { useDevice } from "../features/devices/hooks";

export default function DeviceDetailPage() {
  const { deviceId } = useParams();
  const navigate = useNavigate();
  const { data: device, isLoading, isError } = useDevice(deviceId);

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
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 1 }}
      >
        <Typography variant="h4" component="h1">
          {device.device_name}
        </Typography>
        <Button variant="outlined" onClick={() => navigate(`/devices/${deviceId}/edit`)}>
          Edit
        </Button>
      </Stack>

      <DeviceManagementTabs deviceId={deviceId} />
    </Container>
  );
}
