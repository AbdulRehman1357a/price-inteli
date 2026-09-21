import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useParams, useSearchParams } from "react-router-dom";

import { usePublicPrice } from "../features/outputs/hooks";

// No auth, no MainLayout nav dependency on login state — this is the page a
// customer lands on after scanning a QR code or visiting a Web Output link.
export default function PublicPriceDisplayPage() {
  const { productId } = useParams();
  const [searchParams] = useSearchParams();
  const storeId = searchParams.get("store_id") ?? undefined;
  const { data, isLoading, isError } = usePublicPrice(productId, storeId);

  return (
    <Container maxWidth="xs" sx={{ py: 8 }}>
      <Paper variant="outlined" sx={{ p: 4, textAlign: "center" }}>
        {isLoading && <CircularProgress />}

        {isError && <Alert severity="error">This price page is unavailable.</Alert>}

        {data && (
          <Stack spacing={1} alignItems="center">
            <Typography variant="overline" color="text.secondary">
              {data.sku}
            </Typography>
            <Typography variant="h5">{data.product_name}</Typography>
            <Box sx={{ my: 2 }}>
              <Typography variant="h2" color="primary" sx={{ fontWeight: "bold" }}>
                {data.currency} {data.price}
              </Typography>
            </Box>
            {data.store_name && (
              <Typography variant="body2" color="text.secondary">
                {data.store_name}
              </Typography>
            )}
          </Stack>
        )}
      </Paper>
    </Container>
  );
}
