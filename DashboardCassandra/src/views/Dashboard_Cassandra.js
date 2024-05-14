import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Card, CardHeader, CardBody, CardTitle, Table, Row, Col } from 'reactstrap';
import ChartZoom from 'chartjs-plugin-zoom';
import fetchData from 'variables/charts'; 
const Dashboard = () => {
  const [tableData, setTableData] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [keyspace, setKeyspace] = useState('');
  const [channelName, setChannelName] = useState('');
  const [nazovTabulky, setNazovTabulky] = useState('');
  const [typSignalu, setTypSignalu] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);

  const updateChartData = (data) => {
    // Kontrola, či dáta sú v správnom formáte a obsahujú aspoň jeden záznam
    if (!Array.isArray(data) || data.length === 0 || !data[0].hasOwnProperty('time') || !data[0].hasOwnProperty('value')) {
        console.error('Data is not in the expected format:', data);
        return;
    }

    // Extrahovanie časových značiek a hodnôt z dát
    const labels = data.map(entry => entry.time);
    const values = data.map(entry => entry.value);

    // Vytvorenie aktualizovaných grafických dát
    const updatedChartData = {
        labels: labels,
        datasets: [
            {
                label: 'Values',
                data: values,
                fill: false,
                borderColor: 'rgba(75,192,192,1)',
                tension: 0.1
            }
        ]
    };

    // Nastavenie aktualizovaných grafických dát
    setChartData(updatedChartData);
  };

  useEffect(() => {
    const fetchDataAndUpdateChart = async () => {
      try {
        const data = await fetchData();
        console.log('Data fetched:', data);
        updateChartData(data);
        setTableData(data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchDataAndUpdateChart();
  }, []);

  const options = {
    plugins: {
      zoom: {
        pan: {
          enabled: true,
          mode: 'xy',
          speed: 10
        },
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true
          },
          mode: 'xy',
          sensitivity: 0.2,
          drag: false,
          reverse: true
        }
      }
    },
    onClick: (e, item) => {
      if (item?.length === 0) {
        e.chart.resetZoom();
      }
    }
  };

  return (
    <div className="content">
      <Row>
        <Col lg="12" md="12">
          <Card className="card-chart" style={{ height: '500px' }}>
            <CardHeader>
              <Row>
                <Col className="text-left" sm="6">
                  <CardTitle tag="h2">Kanál {channelName}</CardTitle>
                  <h5 className="card-category"> {keyspace}</h5>
                  <p> {nazovTabulky}</p>
                </Col>
                <Col sm="6"></Col>
              </Row>
            </CardHeader>
            <CardBody>
              <div className="chart-area">
                {chartData && <Line data={chartData} options={options} plugins={[ChartZoom]} />}
              </div>
            </CardBody>
          </Card>
        </Col>
      </Row>
      <Row>
        <Col lg="12" md="12">
          <Card>
            <CardHeader>
              <CardTitle tag="h4">Timestamps</CardTitle>
            </CardHeader>
            <CardBody>
              <Table className="tablesorter" responsive>
                <thead className="text-primary">
                  <tr>
                    <th>Time</th>
                    <th>Values</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(tableData) && tableData.map((entry, index) => (
                    <tr key={index}>
                      <td>{entry.time}</td>
                      <td>{entry.value}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </CardBody>
          </Card>
        </Col>
      </Row>
      <FixedPlugin
        setTableData={setTableData}
        updateChartData={updateChartData}
        setKeyspace={setKeyspace}
        setChannelName={setChannelName}
        setNazovTabulky={setNazovTabulky}
        setTypSignalu={setTypSignalu}
        setMenuOpen={setMenuOpen}
        menuOpen={menuOpen}
      />
    </div>
  );
};

const FixedPlugin = ({ setTableData, updateChartData, setKeyspace, setChannelName, setNazovTabulky, setTypSignalu, setMenuOpen, menuOpen }) => {
  const [keyspaceValue, setKeyspaceValue] = useState('');
  const [nazovTabulkyValue, setNazovTabulkyValue] = useState('');
  const [channelNameValue, setChannelNameValue] = useState('');
  const [typSignaluValue, setTypSignaluValue] = useState('');

  const handleToggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  const handleBucketChange = (event) => {
    setKeyspaceValue(event.target.value);
  };

  const handleRecordingChange = (event) => {
    setNazovTabulkyValue(event.target.value);
  };

  const handleChannelChange = (event) => {
    setChannelNameValue(event.target.value);
  };

  const handleTypSignaluChange = (event) => {
    setTypSignaluValue(event.target.value);
  };

  const handleShowChannelsFFT = async () => {
    try {
      const response = await fetch(`http://localhost:3002/api/${keyspaceValue}/${nazovTabulkyValue}/${channelNameValue}/${typSignaluValue}`);
      const dataFromDB = await response.json();
      console.log('FFT Data from API:', dataFromDB);
      setTableData(dataFromDB);
      updateChartData(dataFromDB);
      setKeyspace(keyspaceValue);
      setChannelName(channelNameValue);
      setNazovTabulky(nazovTabulkyValue);
      setTypSignalu(typSignaluValue);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  return (
    <div className="fixed-plugin">
      <div className="dropdown show">
        <a href="#" className="dropdown-toggle" onClick={handleToggleMenu}>
          <i className="fa fa-cog fa-2x" />
        </a>
        {menuOpen && (
          <ul className="dropdown-menu show">
            <li className="adjustments-line">
              <input
                type="text"
                placeholder="Enter Keyspace Name"
                className="form-control"
                style={{ boxSizing: 'border-box', width: '100%', height: '50px' }}
                value={keyspaceValue}
                onChange={handleBucketChange}
              />
            </li>
            <li className="adjustments-line">
              <input
                type="text"
                placeholder="Enter Recording Name"
                className="form-control"
                style={{ boxSizing: 'border-box', width: '100%', height: '50px' }}
                value={nazovTabulkyValue}
                onChange={handleRecordingChange}
              />
            </li>
            <li className="adjustments-line">
              <input
                type="text"
                placeholder="Enter channel Name"
                className="form-control"
                style={{ boxSizing: 'border-box', width: '100%', height: '50px' }}
                value={channelNameValue}
                onChange={handleChannelChange}
              />
            </li>
            <li className="adjustments-line">
              <input
                type="text"
                placeholder="Enter Signal Type"
                className="form-control"
                style={{ boxSizing: 'border-box', width: '100%', height: '50px' }}
                value={typSignaluValue}
                onChange={handleTypSignaluChange}
              />
            </li>
            <li className="button-container" style={{ marginTop: '10px' }}>
              <button
                className="btn btn-primary btn-block"
                onClick={handleShowChannelsFFT}
              >
                Show
              </button>
            </li>
          </ul>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
