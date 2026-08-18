# FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform

## What this project does
FORESIGHT is an end-to-end demand forecasting and inventory decision-support system for a synthetic retail business.

It:
- ingests relational sales, SKU, store, customer, promotion and inventory data;
- creates a weekly SKU-level demand panel;
- engineers lag, rolling, seasonality and promotion features;
- evaluates a seasonal-naive baseline and LightGBM;
- provides an LSTM deep-learning forecasting path;
- calculates reorder point (ROP) and economic order quantity (EOQ);
- classifies SKUs into reorder, markdown/clear, watch or healthy actions;
- estimates sales-at-risk and locked capital;
- exports replenishment reports;
- serves the results through Streamlit.

## Run
1. Put the supplied CSV files under `data/`.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Open:
   `notebooks/FORESIGHT_End_to_End.ipynb`
4. Run all cells.
5. Start dashboard:
   `streamlit run app/streamlit_app.py`

## Important modelling notes
The supplied engagement brief requires a seasonal-naive baseline, WAPE, rolling-origin backtesting and no leakage. The notebook follows that principle.

The inventory extract does not contain lead time, ordering cost or annual holding cost. Therefore the ROP/EOQ section uses clearly labelled configurable assumptions instead of pretending those values came from the source.

No purchase order is placed automatically.

## Expected outputs
- `outputs/forecast_results.csv`
- `outputs/model_scores.csv`
- `outputs/replenishment_recommendations.csv`
