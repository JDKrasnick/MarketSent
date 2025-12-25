import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import "./index.css";

function App() {
    return (
        <BrowserRouter>
            <div className="container">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                </Routes>
            </div>
        </BrowserRouter>
    );
}

export default App;