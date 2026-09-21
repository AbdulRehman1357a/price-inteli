import VisibilityIcon from "@mui/icons-material/Visibility";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { useIntegrations } from "../features/integrationHub/hooks";
import { PROVIDER_OPTIONS, STATUS_COLORS } from "../features/integrationHub/options";

const providerLabel = (value) => PROVIDER_OPTIONS.find((o) => o.value === value)?.label ?? value;

export default function IntegrationHubListPage() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useIntegrations({ page: 1, pageSize: 50 });

  return (
    <Container sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          Enterprise Integrations
        </Typography>
        <Button variant="contained" component={RouterLink} to="/integration-hub/new">
          New Integration
        </Button>
      </Stack>

      {isError && <Alert severity="error">Unable to load integrations.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Category</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Provider</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Last Sync</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && (data?.items.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No integrations configured yet.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              data?.items.map((integration) => (
                <TableRow key={integration.id} hover>
                  <TableCell>{integration.name}</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {integration.integration_category}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {providerLabel(integration.provider)}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={integration.status}
                      size="small"
                      color={STATUS_COLORS[integration.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {integration.last_sync_at ? new Date(integration.last_sync_at).toLocaleString() : "Never"}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View">
                      <IconButton size="small" onClick={() => navigate(`/integration-hub/${integration.id}`)}>
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
}
