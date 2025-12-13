import axios from "axios";
import { TopTickersResponse, TrendsResponse, TickerSentiment} from "@/types";

const api = axios.create({
    baseURL: "http://localhost:5000/api",
    timeout: 10000,
    headers: {
        "Content-Type": "application/json",
    }
})

export const getTopTickers = async (days: number = 7): Promise<TopTickersResponse> => {
    const response = await api.get('/toptickers', {
        params: { days },  // Becomes ?days=7 in URL
    });
    return response.data;
}

export const getHotPosts = async (time: string = 'week'): Promise<TickerSentiment> => {
    const response = await api.get('/posts', {params: { time }});
    return response.data;
}
