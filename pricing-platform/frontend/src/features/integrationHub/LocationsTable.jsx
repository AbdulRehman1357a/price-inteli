import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import StoreSelect from "../stores/StoreSelect";
import { useDiscoverLocations, useLocations, useUpdateLocation } from "./hooks";

export default function LocationsTable({ integrationId }) {
  const [discoverError, setDiscoverError] = useState(null);
  const { data: locations, isLoading } = useLocations(integrationId);
  const discoverLocations = useDiscoverLocations(integrationId);
  const updateLocation = useUpdateLocation(integrationId);

  const handleDiscover = async () => {
    setDiscoverError(null);
    try {
      await discoverLocations.mutateAsync();
    } catch (error) {
      setDiscoverError(error.response?.data?.error?.message ?? "Unable to discover locations.");
    }
  };

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={2} alignItems="center">
        <Button variant="outlined" onClick={handleDiscover} disabled={discoverLocations.isPending}>
          {discoverLocations.isPending ? "Discovering…" : "Discover Locations"}
        </Button>
        <Typography variant="body2" color="text.secondary">
          Pulls store/location records from the connected system and lists them below for mapping.
        </Typography>
      </Stack>
      {discoverError && <Alert severity="error">{discoverError}</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>External Location</TableCell>
              <TableCell>Mapped PIP Store</TableCell>
              <TableCell align="center">Sync Enabled</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {!isLoading && (locations ?? []).length === 0 && (
              <TableRow>
                <TableCell colSpan={3} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    No locations discovered yet — click "Discover Locations" above.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {(locations ?? []).map((location) => (
              <TableRow key={location.id}>
                <TableCell>
                  {location.external_location_name}
                  <Chip
                    label={location.external_location_id}
                    size="small"
                    variant="outlined"
                    sx={{ ml: 1 }}
                  />
                </TableCell>
                <TableCell sx={{ minWidth: { xs: 160, sm: 220 } }}>
                  <StoreSelect
                    value={location.store_id}
                    onChange={(storeId) =>
                      updateLocation.mutate({ locationId: location.id, payload: { store_id: storeId || null } })
                    }
                  />
                </TableCell>
                <TableCell align="center">
                  <Switch
                    checked={location.is_active}
                    onChange={(event) =>
                      updateLocation.mutate({
                        locationId: location.id,
                        payload: { is_active: event.target.checked },
                      })
                    }
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
