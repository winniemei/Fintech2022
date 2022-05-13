{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "34d961b5-775d-4303-8ddf-e929334d28e2",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Import libraries and dependencies\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "import os\n",
    "import alpaca_trade_api as tradeapi\n",
    "import datetime as dt\n",
    "import pytz\n",
    "class MCSimulation:\n",
    "    “”\"\n",
    "    A Python class for runnning Monte Carlo simulation on portfolio price data.\n",
    "    ...\n",
    "    Attributes\n",
    "    ----------\n",
    "    portfolio_data : pandas.DataFrame\n",
    "        portfolio dataframe\n",
    "    weights: list(float)\n",
    "        portfolio investment breakdown\n",
    "    nSim: int\n",
    "        number of samples in simulation\n",
    "    nTrading: int\n",
    "        number of trading days to simulate\n",
    "    simulated_return : pandas.DataFrame\n",
    "        Simulated data from Monte Carlo\n",
    "    confidence_interval : pandas.Series\n",
    "        the 95% confidence intervals for simulated final cumulative returns\n",
    "    “”\"\n",
    "    def __init__(self, portfolio_data, weights=“”, num_simulation=1000, num_trading_days=252):\n",
    "        “”\"\n",
    "        Constructs all the necessary attributes for the MCSimulation object.\n",
    "        Parameters\n",
    "        ----------\n",
    "        portfolio_data: pandas.DataFrame\n",
    "            DataFrame containing stock price information from Alpaca API\n",
    "        weights: list(float)\n",
    "            A list fractions representing percentage of total investment per stock. DEFAULT: Equal distribution\n",
    "        num_simulation: int\n",
    "            Number of simulation samples. DEFAULT: 1000 simulation samples\n",
    "        num_trading_days: int\n",
    "            Number of trading days to simulate. DEFAULT: 252 days (1 year of business days)\n",
    "        “”\"\n",
    "        # Check to make sure that all attributes are set\n",
    "        if not isinstance(portfolio_data, pd.DataFrame):\n",
    "            raise TypeError(“portfolio_data must be a Pandas DataFrame”)\n",
    "        # Set weights if empty, otherwise make sure sum of weights equals one.\n",
    "        if weights == “”:\n",
    "            num_stocks = len(portfolio_data.columns.get_level_values(0).unique())\n",
    "            weights = [1.0/num_stocks for s in range(0,num_stocks)]\n",
    "        else:\n",
    "            if round(sum(weights),2) < .99:\n",
    "                raise AttributeError(“Sum of portfolio weights must equal one.“)\n",
    "        # Calculate daily return if not within dataframe\n",
    "        if not “daily_return” in portfolio_data.columns.get_level_values(1).unique():\n",
    "            close_df = portfolio_data.xs(‘close’,level=1,axis=1).pct_change()\n",
    "            tickers = portfolio_data.columns.get_level_values(0).unique()\n",
    "            column_names = [(x,“daily_return”) for x in tickers]\n",
    "            close_df.columns = pd.MultiIndex.from_tuples(column_names)\n",
    "            portfolio_data = portfolio_data.merge(close_df,left_index=True,right_index=True).reindex(columns=tickers,level=0)\n",
    "        # Set class attributes\n",
    "        self.portfolio_data = portfolio_data\n",
    "        self.weights = weights\n",
    "        self.nSim = num_simulation\n",
    "        self.nTrading = num_trading_days\n",
    "        self.simulated_return = “”\n",
    "    def calc_cumulative_return(self):\n",
    "        “”\"\n",
    "        Calculates the cumulative return of a stock over time using a Monte Carlo simulation (Brownian motion with drift).\n",
    "        “”\"\n",
    "        # Get closing prices of each stock\n",
    "        last_prices = self.portfolio_data.xs(‘close’,level=1,axis=1)[-1:].values.tolist()[0]\n",
    "        # Calculate the mean and standard deviation of daily returns for each stock\n",
    "        daily_returns = self.portfolio_data.xs(‘daily_return’,level=1,axis=1)\n",
    "        mean_returns = daily_returns.mean().tolist()\n",
    "        std_returns = daily_returns.std().tolist()\n",
    "        # Initialize empty Dataframe to hold simulated prices\n",
    "        portfolio_cumulative_returns = pd.DataFrame()\n",
    "        # Run the simulation of projecting stock prices ‘nSim’ number of times\n",
    "        for n in range(self.nSim):\n",
    "            if n % 10 == 0:\n",
    "                print(f”Running Monte Carlo simulation number {n}.“)\n",
    "            # Create a list of lists to contain the simulated values for each stock\n",
    "            simvals = [[p] for p in last_prices]\n",
    "            # For each stock in our data:\n",
    "            for s in range(len(last_prices)):\n",
    "                # Simulate the returns for each trading day\n",
    "                for i in range(self.nTrading):\n",
    "                    # Calculate the simulated price using the last price within the list\n",
    "                    simvals[s].append(simvals[s][-1] * (1 + np.random.normal(mean_returns[s], std_returns[s])))\n",
    "            # Calculate the daily returns of simulated prices\n",
    "            sim_df = pd.DataFrame(simvals).T.pct_change()\n",
    "            # Use the `dot` function with the weights to multiply weights with each column’s simulated daily returns\n",
    "            sim_df = sim_df.dot(self.weights)\n",
    "            # Calculate the normalized, cumulative return series\n",
    "            portfolio_cumulative_returns[n] = (1 + sim_df.fillna(0)).cumprod()\n",
    "        # Set attribute to use in plotting\n",
    "        self.simulated_return = portfolio_cumulative_returns\n",
    "        # Calculate 95% confidence intervals for final cumulative returns\n",
    "        self.confidence_interval = portfolio_cumulative_returns.iloc[-1, :].quantile(q=[0.025, 0.975])\n",
    "        return portfolio_cumulative_returns\n",
    "    def plot_simulation(self):\n",
    "        “”\"\n",
    "        Visualizes the simulated stock trajectories using calc_cumulative_return method.\n",
    "        “”\"\n",
    "        # Check to make sure that simulation has run previously.\n",
    "        if not isinstance(self.simulated_return,pd.DataFrame):\n",
    "            self.calc_cumulative_return()\n",
    "        # Use Pandas plot function to plot the return data\n",
    "        plot_title = f”{self.nSim} Simulations of Cumulative Portfolio Return Trajectories Over the Next {self.nTrading} Trading Days.”\n",
    "        return self.simulated_return.plot(legend=None,title=plot_title)\n",
    "    def plot_distribution(self):\n",
    "        “”\"\n",
    "        Visualizes the distribution of cumulative returns simulated using calc_cumulative_return method.\n",
    "        “”\"\n",
    "        # Check to make sure that simulation has run previously.\n",
    "        if not isinstance(self.simulated_return,pd.DataFrame):\n",
    "            self.calc_cumulative_return()\n",
    "        # Use the `plot` function to create a probability distribution histogram of simulated ending prices\n",
    "        # with markings for a 95% confidence interval\n",
    "        plot_title = f”Distribution of Final Cumuluative Returns Across All {self.nSim} Simulations”\n",
    "        plt = self.simulated_return.iloc[-1, :].plot(kind=‘hist’, bins=10,density=True,title=plot_title)\n",
    "        plt.axvline(self.confidence_interval.iloc[0], color=‘r’)\n",
    "        plt.axvline(self.confidence_interval.iloc[1], color=‘r’)\n",
    "        return plt\n",
    "    def summarize_cumulative_return(self):\n",
    "        “”\"\n",
    "        Calculate final summary statistics for Monte Carlo simulated stock data.\n",
    "        “”\"\n",
    "        # Check to make sure that simulation has run previously.\n",
    "        if not isinstance(self.simulated_return,pd.DataFrame):\n",
    "            self.calc_cumulative_return()\n",
    "        metrics = self.simulated_return.iloc[-1].describe()\n",
    "        ci_series = self.confidence_interval\n",
    "        ci_series.index = [“95% CI Lower”,“95% CI Upper”]\n",
    "        return metrics.append(ci_series)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": ""
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}