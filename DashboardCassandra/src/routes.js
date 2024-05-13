

import DashboardCassandra from "views/Dashboard_Cassandra";

var routes = [
 
  
  {
    path: "/dashboardCassandra",
    name: "Dashboard Cassandra",

    icon: "tim-icons icon-chart-pie-36",
    component: <DashboardCassandra />,
   
    layout: "/admin",
  },
];
export default routes;
