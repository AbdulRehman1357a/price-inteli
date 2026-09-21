import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import InventoryIcon from "@mui/icons-material/Inventory2";
import VisibilityIcon from "@mui/icons-material/Visibility";
import Alert from "@mui/material/Alert";
import Avatar from "@mui/material/Avatar";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TableSortLabel from "@mui/material/TableSortLabel";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { useAllCategories } from "../features/categories/hooks";
import { flattenCategoryTree } from "../features/categories/tree";
import { useDeleteProduct, useProducts } from "../features/products/hooks";
import { PRODUCT_STATUS_OPTIONS } from "../features/products/options";

const STATUS_COLORS = { active: "success", inactive: "default", discontinued: "error" };

const SORTABLE_COLUMNS = [
  { key: "product_name", label: "Product Name" },
  { key: "sku", label: "SKU" },
  { key: "selling_price", label: "Selling Price" },
];

export default function ProductsListPage() {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [status, setStatus] = useState("");
  const [sortKey, setSortKey] = useState("created_at");
  const [sortDir, setSortDir] = useState("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [productToDelete, setProductToDelete] = useState(null);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchInput]);

  const sort = `${sortDir === "desc" ? "-" : ""}${sortKey}`;
  const { data, isLoading, isError } = useProducts({
    page,
    pageSize,
    search,
    categoryId,
    status,
    sort,
  });
  const { data: categories } = useAllCategories();
  const categoryOptions = useMemo(() => flattenCategoryTree(categories ?? []), [categories]);
  const categoryNameById = useMemo(
    () => new Map((categories ?? []).map((c) => [c.id, c.name])),
    [categories]
  );

  const deleteProduct = useDeleteProduct();

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
    setPage(1);
  };

  const handleConfirmDelete = async () => {
    if (!productToDelete) return;
    await deleteProduct.mutateAsync(productToDelete.id);
    setProductToDelete(null);
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
          Products
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button
            variant="outlined"
            component={RouterLink}
            to="/imports/new"
            state={{ entityType: "products" }}
          >
            Bulk Import
          </Button>
          <Button variant="contained" component={RouterLink} to="/products/new">
            New Product
          </Button>
        </Stack>
      </Stack>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}>
        <TextField
          label="Search"
          placeholder="SKU, barcode, or product name"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          sx={{ minWidth: { xs: "100%", sm: 260 } }}
        />
        <TextField
          select
          label="Category"
          value={categoryId}
          onChange={(event) => {
            setCategoryId(event.target.value);
            setPage(1);
          }}
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
        <TextField
          select
          label="Status"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
          sx={{ minWidth: { xs: "100%", sm: 160 } }}
        >
          <MenuItem value="">All statuses</MenuItem>
          {PRODUCT_STATUS_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {isError && <Alert severity="error">Unable to load products.</Alert>}

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Image</TableCell>
              {SORTABLE_COLUMNS.map((column) => (
                <TableCell key={column.key}>
                  <TableSortLabel
                    active={sortKey === column.key}
                    direction={sortKey === column.key ? sortDir : "asc"}
                    onClick={() => handleSort(column.key)}
                  >
                    {column.label}
                  </TableSortLabel>
                </TableCell>
              ))}
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Barcode</TableCell>
              <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>Category</TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>Cost Price</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No products found.</Typography>
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              data?.items.map((product) => (
                <TableRow key={product.id} hover>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    <Avatar src={product.product_image_url || undefined} variant="rounded">
                      <InventoryIcon fontSize="small" />
                    </Avatar>
                  </TableCell>
                  <TableCell>{product.product_name}</TableCell>
                  <TableCell>{product.sku}</TableCell>
                  <TableCell>
                    {product.selling_price} {product.currency || ""}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {product.barcode || "—"}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", sm: "table-cell" } }}>
                    {categoryNameById.get(product.category_id) || "—"}
                  </TableCell>
                  <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}>
                    {product.cost_price ?? "—"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={product.status}
                      size="small"
                      color={STATUS_COLORS[product.status] ?? "default"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View">
                      <IconButton size="small" onClick={() => navigate(`/products/${product.id}`)}>
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => navigate(`/products/${product.id}/edit`)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => setProductToDelete(product)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
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

      <Dialog open={Boolean(productToDelete)} onClose={() => setProductToDelete(null)}>
        <DialogTitle>Delete product</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete <strong>{productToDelete?.product_name}</strong> ({productToDelete?.sku})? This can't
            be undone from here.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProductToDelete(null)}>Cancel</Button>
          <Button color="error" onClick={handleConfirmDelete} disabled={deleteProduct.isPending}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
