import React from 'react';
import PropTypes from 'prop-types';
import Humanize from 'humanize-plus';

import { withStyles } from '@material-ui/core/styles';

import {Chart} from "react-google-charts";
import BodySection from '../components/BodySection';
import Page from "../containers/Page";
import FetchMediaItem from '../containers/FetchMediaItem';
import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableRow from '@material-ui/core/TableRow';
import ShowChartIcon from '@material-ui/icons/ShowChart';
import {ANALYTICS_FROM_PAGE} from "../api";
import Typography from '@material-ui/core/Typography';

/**
 * The media item's analytics page
 */
const AnalyticsPage = ({ match: { params: { pk } } }) => (
  <Page>
    <FetchMediaItem id={ pk } component={ ConnectedAnalyticsPageContents } />
  </Page>
);

/**
 * The media item's analytics page contents
 */
const AnalyticsPageContents = ({
  classes,
  analytics: { viewsPerDay, size, totalViews },
  resource: mediaItem
}) => (
  <div>
    <BodySection classes={{ root: classes.section }}>
      <Typography variant="headline" component="div">
        { mediaItem && mediaItem.title }
      </Typography>
    </BodySection>
    <BodySection classes={{ root: classes.section }}>
      <Typography variant="title" component="div" gutterBottom >
        General Statistics
      </Typography>
      <Grid container>
        <Grid item xs={12} sm={6} md={3} lg={2}>
          <Paper>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell>Total Views</TableCell>
                  <TableCell numeric>{ totalViews }</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Total Size</TableCell>
                  <TableCell numeric>{ Humanize.fileSize(size) }</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>
    </BodySection>
    <BodySection classes={{ root: classes.section }}>
      <div className={ classes.chartContainer }>
        <Typography variant="title" component="div" gutterBottom >
          Viewing history (views per day)
        </Typography>
        {
          viewsPerDay.length > 1
          ?
            <Typography variant='body1' component='div'>
              <Chart
                chartType="AnnotationChart"
                data={viewsPerDay}
                options={{fill: 100, colors: ['#EF2E31']}}
              />
            </Typography>
          :
          <Typography variant="subheading">
            There is no data available for the media
          </Typography>
      }
      </div>
    </BodySection>
    <BodySection classes={{ root: classes.section }}>
      <Grid container justify='space-between' spacing={16}>
        <Grid item xs={12} sm={6} md={3} lg={2}/>
        <Grid item xs={12} sm={6} md={3} lg={2} style={{textAlign: 'right'}}>
          {
            mediaItem && mediaItem.legacyStatisticsUrl
            ?
            <Button component='a' variant='outlined' className={ classes.link } fullWidth
              href={mediaItem.legacyStatisticsUrl}
            >
              SMS Statistics
              <ShowChartIcon className={ classes.rightIcon } />
            </Button>
            :
            null
          }
        </Grid>
      </Grid>
    </BodySection>
  </div>
);

AnalyticsPageContents.propTypes = {
  analytics: PropTypes.shape({
    size: PropTypes.number,
    totalViews: PropTypes.number,
    viewsPerDay: PropTypes.arrayOf(PropTypes.array),
  }).isRequired,
  classes: PropTypes.object.isRequired,
};

/**
 * A higher-order component wrapper which retrieves the media item's analytics (resolved from
 * global data), generates the chart data for AnnotationChart, and passes it along.
 */
const withAnalytics = WrappedComponent => props => {

  const analytics = {
    size: ANALYTICS_FROM_PAGE.size,
    totalViews: 0,
    viewsPerDay: [["Date", "Views"]],
  };

  let minDate = new Date("9999-12-31");
  let maxDate = new Date("0000-01-01");

  const summedByDate = {};

  if (
    ANALYTICS_FROM_PAGE.views_per_day.length > 0
  ) {
    const views_per_day = ANALYTICS_FROM_PAGE.views_per_day;
    // Here we sum up all views for a particular day (irrespective of other variable) and
    // calculate the min and max dates.
    for (let i = 0; i < ANALYTICS_FROM_PAGE.views_per_day.length; i ++) {
      const date = new Date(ANALYTICS_FROM_PAGE.views_per_day[i].date);
      const views = date in summedByDate ? summedByDate[date] : 0;
      summedByDate[date] = views + ANALYTICS_FROM_PAGE.views_per_day[i].views;
      minDate = Math.min(minDate, date);
      maxDate = Math.max(maxDate, date);
      analytics.totalViews += ANALYTICS_FROM_PAGE.views_per_day[i].views
    }

    // Here we provide an ordered list of the views fill out missing days with zero views.

    // Note we also add a zero data-point at either end of the data which makes the graph
    // look better in case of a single data-point.
    maxDate = addDays(new Date(maxDate), 1);
    let currentDate = addDays(new Date(minDate), -1);

    while (currentDate <= maxDate) {
      analytics.viewsPerDay.push(
        [currentDate, currentDate in summedByDate ? summedByDate[currentDate] : 0]
      );
      currentDate = addDays(currentDate, 1);
    }
  }

  return (<WrappedComponent analytics={analytics} {...props} />);
};

/**
 * A helper function to return a new date displaced from a given date by given number of days.
 */
const addDays = (date, days) => {
    const result = new Date(date.valueOf());
    result.setUTCDate(result.getUTCDate() + days);
    return result;
};

/* tslint:disable object-literal-sort-keys */
var styles = theme => ({
  section: {
    marginTop: theme.spacing.unit * 2,
  },
  chartContainer: {
    /* Missing bottom border */
    '& .rangeControl': {
      borderBottom: [['1px', '#888888', 'solid']]
    },
    /**
     * Hide the useless displayZoomButtons
     *
     * HACK: it is noted here that this approach is brittle - keep an eye on Google Charts in case
     * they provide a way of configuring these buttons in the future (alternatively we could make
     * our own buttons using setVisibleChartRange()).
     */
    '& #reactgooglegraph-1_AnnotationChart_zoomControlContainer_1-hour': {
      display: 'none'
    },
    '& #reactgooglegraph-1_AnnotationChart_zoomControlContainer_1-day': {
      display: 'none'
    },
    '& #reactgooglegraph-1_AnnotationChart_zoomControlContainer_5-days': {
      display: 'none'
    }
  },
  link: {
    color: theme.palette.text.secondary,
  },
  rightIcon: {
    marginLeft: theme.spacing.unit,
  }
});
/* tslint:enable */

const ConnectedAnalyticsPageContents = withAnalytics(withStyles(styles)(AnalyticsPageContents));

export default AnalyticsPage;
