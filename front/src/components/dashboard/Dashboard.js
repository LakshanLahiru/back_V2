import React, { useState, useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import './Dashboard.css';
import Navi from '../navibar/Navi';


const Dashboard = () => {
    
    const [profit, setProfit] = useState(null);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const fetchProfit = () => {
        console.log(startDate)
        console.log(endDate);
        // Perform API call to fetch profit data based on selected dates
        fetch(`/api/profit?startDate=${startDate}&endDate=${endDate}`)
            
            .then(response => response.json())
            .then(data => {
                console.log('Fetched profit:', data); // Debugging log
                setProfit(data[0][0]); // Assuming the API returns profit as an object with a key 'total_profit'
            })
            .catch(error => console.error('Error:', error));
    };



    const handleStartDateChange = (event) => {
        setStartDate(event.target.value);
        
    };

    const handleEndDateChange = (event) => {
        setEndDate(event.target.value);
        
    };





    return (
        <div>
           <Navi/>
       
        <div className='container'>
          <center>
            

            <h1>Profit</h1>
                <div>
                    <label><h3>Start Date :</h3></label>
                    <input className='date' type="date" value={startDate} onChange={handleStartDateChange} />
                </div>
                <div>
                    <label><h3>End  Date   : </h3></label>
                    
                    <input  className='date1' type="date" value={endDate} onChange={handleEndDateChange} />
                </div>
                <br></br>
                <Button variant="success" onClick={fetchProfit} >Show Profit</Button>{' '}
                {profit !== null ? (
                    <h2>Profit: {profit.toFixed(2)} USDT</h2>
                ) : (
                    <p>Loading...</p>
                )}

          </center>

        </div>
        </div>
    );
};

export default Dashboard;
