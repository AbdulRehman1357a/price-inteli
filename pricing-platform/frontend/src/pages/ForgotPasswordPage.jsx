import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Link from "@mui/material/Link";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    // Placeholder only — password reset is not implemented yet.
    setSubmitted(true);
  };

  return (
    <Container maxWidth="xs" sx={{ py: 8 }}>
      <Paper variant="outlined" sx={{ p: 4 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          Forgot password
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Password reset is coming in a future phase. This form is a placeholder.
        </Typography>

        {submitted ? (
          <Typography>If an account exists for that email, a reset link will be sent.</Typography>
        ) : (
          <Box component="form" onSubmit={handleSubmit} noValidate>
            <Stack spacing={2}>
              <TextField
                label="Email"
                type="email"
                fullWidth
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
              <Button type="submit" variant="contained" size="large">
                Send reset link
              </Button>
            </Stack>
          </Box>
        )}

        <Stack sx={{ mt: 3 }}>
          <Link component={RouterLink} to="/login" variant="body2">
            Back to sign in
          </Link>
        </Stack>
      </Paper>
    </Container>
  );
}
