import {useState, useEffect} from "react";
import axios from "axios";


function App() {

    const [array, setArray] = useState([]);


    const fetchAPI = async () => {
        const response = await axios.get("http://localhost:5000/api/health");
        setArray(response.data);
    }

    useEffect(() => {
        fetchAPI();
    }, []);

    return (
      <div>
        <h1>MarketSent Dashboard</h1>
          <p>
              Status: {array.status}
              <p></p>
              DB Connection Status: {array.database}
          </p>
      </div>
    )
  }

  export default App
