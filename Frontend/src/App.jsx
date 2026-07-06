import "./App.css";
import Start from "./Pages/start.jsx";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AddProductOption from "./Components/AddProduct/AddProductOption.jsx";
import SalesHistoryOption from "./Components/SalesHistory/SalesHistoryOption.jsx";
import ScanProductsOption from "./Components/ScanProducts/ScanProductsOption.jsx";
import LastSalesOption from "./Components/LastSales/LastSalesOption.jsx";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Start />} />
        <Route path="/add-product" element={<AddProductOption />} />
        <Route path="/sales-history" element={<SalesHistoryOption />} />
        <Route path="/scan-products" element={<ScanProductsOption />} />
        <Route path="/last-sales" element={<LastSalesOption />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
