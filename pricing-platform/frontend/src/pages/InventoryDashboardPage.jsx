import InventoryIcon from "@mui/icons-material/Inventory2";
import ReportProblemIcon from "@mui/icons-material/ReportProblem";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import FormControlLabel from "@mui/material/FormControlLabel";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { useAllCategories } from "../features/categories/hooks";
import { flattenCategoryTree } from "../features/categories/tree";
import { useInventoryList, useInventorySummary } from "../features/inventory/hooks";
import { INVENTORY_STATUS_COLORS, INVENTORY_STATUS_LABELS } from "../features/inventory/options";
import { useAllStores } from "../features/stores/hooks";

function SummaryCard({ icon, label, value, color }) {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" spacing={2} alignItems="center">
        <Stack
          sx={{
            width: 44,
            height: 44,
            borderRadius: 2,
            bgcolor: `${color}.main`,
            color: `${color}.contrastText`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {icon}
        </Stack>
        <Stack>
          <Typography variant="h5">{value ?? "—"}</Typography>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
        </Stack>
      </Stack>
    </Paper>
  );
}

export default function InventoryDashboardPage() {
  const [storeId, setStoreId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [lowStock, setLowStock] = useState(false);
  const [outOfStock, setOutOfStock] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const filters = { storeId, categoryId, lowStock, outOfStock };
  const { data, isLoading, isError } = useInventoryList({ page, pageSize, ...filters });
  const { data: summary } = useInventorySummary({ storeId, categoryId });
  const { data: stores } = useAllStores();
  const { data: categories } = useAllCategories();
  const categoryOptions = useMemo(() => flattenCategoryTree(categories ?? []), [categories]);

  const updateFilter = (setter) => (value) => {
    setter(value);
    setPage(1);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" component="h1">
          Inventory
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button
            variant="outlined"
            component={RouterLink}
            to="/imports/new"
            state={{ entityType: "inventory" }}
          >
            Bulk Import
          </Button>
          <Button variant="contained" component={RouterLink} to="/inventory/adjust">
            Adjust Stock
          </Button>
        </Stack>
      </Stack>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            icon={<InventoryIcon />}
            label="Total Products"
            value={summary?.total_products}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            icon={<TrendingDownIcon />}
            label="Low Stock"
            value={summary?.low_stock}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            icon={<ReportProblemIcon />}
            label="Out of Stock"
            value={summary?.out_of_stock}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            icon={<TrendingUpIcon />}
            label="Overstock"
            value={summary?.overstock}
            color="info"
          />
        </Grid>
      </Grid>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems={{ sm: "center" }} sx={{ mb: 2 }}>
        <TextField
          select
          label="Store"
          value={storeId}
          onChange={(event) => updateFilter(setStoreId)(event.target.value)}
          sx={{ minWidth: { xs: "100%", sm: 200 } }}
        >
          <MenuItem value="">All stores</MenuItem>
          {(stores ?? []).map((store) => (
            <MenuItem key={store.id} value={store.id}>
              {store.name}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Category"
          value={categoryId}
          onChange={(event) => updateFilter(setCategoryId)(event.target.value)}
          sx={{ minWidth: { xs: "100%", sm: 200 } }}
        >
          <MenuItem value="">All categories</MenuItem>
          {categoryOptions.map((option) => (
            <MenuItem key={option.id} value={option.id}>
              {"— ".repeat(option.depth)}
              {option.name}
            </MenuItem>
          ))}
        </TextField>
        <FormControlLabel
          control={
            <Switch checked={lowStock} onChange={(event) => updateFilter(setLowStock)(event.target.checked)} />
          }
          label="Low stock only"
        />
        <FormControlLabel
          control={
            <Switch
              checked={outOfStock}
              onChange={(event) => updateFilter(setOutOfStock)(event.target.checked)}
            />
          }
          label="Out of stock only"
        />
      </Stack>

      {isError && <Alert severity="error">Unable to load inventory.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>SKU</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Store</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                On Hand
              </TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                Reserved
              </TableCell>
              <TableCell align="right">Available</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                Reorder Point
              </TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                Safety Stock
              </TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Last Updated</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No inventory records found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              data?.items.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>{item.product_name}</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>{item.product_sku}</TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {item.store_name} ({item.store_code})
                  </TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {item.quantity_on_hand}
                  </TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {item.quantity_reserved}
                  </TableCell>
                  <TableCell align="right">{item.quantity_available}</TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {item.reorder_point ?? "—"}
                  </TableCell>
                  <TableCell align="right" sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {item.safety_stock ?? "—"}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {item.last_stock_update_at
                      ? new Date(item.last_stock_update_at).toLocaleString()
                      : "—"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={INVENTORY_STATUS_LABELS[item.status] ?? item.status}
                      size="small"
                      color={INVENTORY_STATUS_COLORS[item.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.meta?.total ?? 0}
          page={page - 1}
          onPageChange={(_, newPage) => setPage(newPage + 1)}
          rowsPerPage={pageSize}
          onRowsPerPageChange={(event) => {
            setPageSize(Number(event.target.value));
            setPage(1);
          }}
          rowsPerPageOptions={[10, 20, 50]}
        />
      </TableContainer>
    </Container>
  );
}
