import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import ChannelForm, { channelToFormValues } from "../features/outputs/ChannelForm";
import { useChannel, useUpdateChannel } from "../features/outputs/hooks";

export default function OutputChannelEditPage() {
  const { channelId } = useParams();
  const navigate = useNavigate();
  const { data: channel, isLoading, isError } = useChannel(channelId);
  const updateChannel = useUpdateChannel(channelId);

  const handleSubmit = async (payload) => {
    await updateChannel.mutateAsync(payload);
    navigate("/outputs/channels", { replace: true });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !channel) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Output channel not found.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit Output
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <ChannelForm
          defaultValues={channelToFormValues(channel)}
          onSubmit={handleSubmit}
          submitLabel="Save Changes"
        />
      </Paper>
    </Container>
  );
}
