import logging

from selenium.webdriver.common.by import By

from covid19_scrapers.scraper import ScraperBase
from covid19_scrapers.utils import arcgis, misc, tableau
from covid19_scrapers.webdriver import WebdriverRunner, WebdriverSteps

_logger = logging.getLogger(__name__)


class NewJersey(ScraperBase):
    """New Jersey publishes total COVID-19 case and death counts
    via an ArcGIS. The demographic breakdowns for cases are obtained via OCR
    while demographic breakdowns for deaths for deaths are obtained via Tableau
    """

    # ArcGIS service is at https://services7.arcgis.com/Z0rixLlManVefxqY
    TOTALS = dict(
        flc_id='6ed094967200492288b0978261b2b1e7',
        layer_name='survey',
        where='total_deaths IS NOT NULL and total_positives IS NOT NULL',
        order_by='CreationDate desc',
        offset=0,
        limit=1,
        out_fields=['total_deaths, total_positives, EditDate'])

    DEATHS_URL = 'https://public.tableau.com/views/UnderlyingCauses/COVID-19DeathsbyRace?%3Aembed=y&%3AshowVizHome=no'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def name(self):
        return 'New Jersey'

    def _scrape(self, **kwargs):
        _, totals_df = arcgis.query_geoservice(**self.TOTALS)
        date = totals_df.loc[0, 'EditDate'].date()
        cases = totals_df.loc[0, 'total_positives']
        deaths = totals_df.loc[0, 'total_deaths']

        runner = WebdriverRunner()
        results = runner.run(
            WebdriverSteps()
            .go_to_url(self.DEATHS_URL)
            .wait_for_number_of_elements((By.XPATH, '//canvas'), 3)
            .find_request('deaths', find_by=tableau.find_tableau_request)
        )

        parser = tableau.TableauParser(request=results.requests['deaths'])
        df = parser.get_dataframe_from_key('COVID-19 Deaths by Race')
        df.columns = ['Race', 'Deaths', 'Percent']
        df['Race'] = df['Race'].apply(lambda race: race.strip())
        df = df.set_index('Race')
        aa_deaths = df.loc['Black (non-Hispanic)', 'Deaths']
        known_race_deaths = df['Deaths'].sum()

        pct_aa_deaths = misc.to_percentage(aa_deaths, known_race_deaths)

        return [self._make_series(
            date=date,
            cases=cases,
            deaths=deaths,
            # aa_cases=aa_cases,
            aa_deaths=aa_deaths,
            # pct_aa_cases=aa_cases_pct,
            pct_aa_deaths=pct_aa_deaths,
            # pct_includes_unknown_race=False,
            # pct_includes_hispanic_black=False,
        )]
