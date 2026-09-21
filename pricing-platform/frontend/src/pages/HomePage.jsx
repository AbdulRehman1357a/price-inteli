import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";

export default function HomePage() {
  return (
    <Container sx={{ py: 6 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Retail Pricing Intelligence Platform
      </Typography>
      <Typography color="text.secondary">Application skeleton is running.</Typography>
    </Container>
  );
}
