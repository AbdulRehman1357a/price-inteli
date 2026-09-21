import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";

export default function NotFoundPage() {
  return (
    <Container sx={{ py: 6 }}>
      <Typography variant="h5" component="h1">
        Page not found
      </Typography>
    </Container>
  );
}
