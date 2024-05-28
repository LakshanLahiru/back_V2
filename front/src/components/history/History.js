import React, { useState, useEffect } from 'react';
import Table from 'react-bootstrap/Table';
import Navi from '../navibar/Navi';

const History = () => {
    const [data, setData] = useState([]);

    useEffect(() => {
        fetch('/api/data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Fetched data:', data);
                setData(data);
            })
            .catch(error => console.error('Error fetching data:', error));
    }, []);

    console.log('Data in state:', data); // Debugging log

    return (
        <div>
            <Navi/>
         
        <div className='container'>
            <center><h1>Historical Data</h1></center>

            <Table striped bordered hover variant="dark" >
                <thead>
                    <tr>
                        
                        <th>Open Time</th>
                        <th>Close Time</th>
                        <th>Entry Price</th>
                        <th>Closed Price</th>
                        <th>Decision</th>
                        <th>Side</th>
                        <th>Profit</th>
                        <th>ROI(%)</th>
                        {/* Add more table headers as needed */}
                    </tr>
                </thead>
                <tbody>
                {data.map((row, index) => (
                        <tr key={index}>
                            <td>{row[0]}</td>
                            <td>{row[1]}</td>
                            <td>{row[2]}</td>
                            <td>{row[3]}</td>
                            <td>{row[4]}</td>
                            <td>{row[5]}</td>
                            <td>{row[6]}</td>
                            <td>{row[7]}</td>
                           
                            {/* Add more table cells based on your data structure */}
                        </tr>
                    ))}
                </tbody>
            </Table>
        </div>
        </div>
    );
};

export default History;
