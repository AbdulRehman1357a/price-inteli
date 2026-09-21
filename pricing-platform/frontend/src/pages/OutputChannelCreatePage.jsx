import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import ChannelForm from "../features/outputs/ChannelForm";
import { useCreateChannel } from "../features/outputs/hooks";

export default function OutputChannelCreatePage() {
  const navigate = useNavigate();
  const createChannel = useCreateChannel();

  const handleSubmit = async (payload) => {
    const channel = await createChannel.mutateAsync(payload);
    navigate(`/outputs/channels/${channel.id}/edit`, { replace: true });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New Output
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <ChannelForm onSubmit={handleSubmit} submitLabel="Create Output" isCreate />
      </Paper>
    </Container>
  );
}
