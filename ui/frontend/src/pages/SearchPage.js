import React, { Component } from 'react';

import Chip from '@material-ui/core/Chip';
import Grid from '@material-ui/core/Grid';
import MenuList from '@material-ui/core/MenuList';
import MenuItem from '@material-ui/core/MenuItem';
import Paper from '@material-ui/core/Paper';
import { withStyles } from '@material-ui/core/styles';

import BodySection from '../components/BodySection';
import FetchChannels from "../containers/FetchChannels";
import FetchPlaylists from "../containers/FetchPlaylists";
import FetchMediaItems from "../containers/FetchMediaItems";
import Page from "../containers/Page";

// The different categories of search results and their FetchResources component.
const categories = [
  ['Media', FetchMediaItems],
  ['Channels', FetchChannels],
  ['Playlists', FetchPlaylists],
];

// check to see if there are any search params
const params = new URLSearchParams(location.search);
const windowSearchParam = params.get('q');
const searchQuery = { search: windowSearchParam };

/**
 * The page for displaying the search results. It retrieves the media items, playlists, and
 * channels for the search critieria simultaneously and initially shows the media items to the
 * user. A left-hand panel is provided to navigate between the different categories of results.
 */
class SearchPage extends Component {
  state = {
    // Counts of the search results keyed on category
    categoryCounts: {},
    // The selected result category
    selectedCategory: 'Media',
  };

  handleSelected = category => () => {
    this.setState({'selectedCategory' : category});
  };

  handleFetched = category => (listResponse) => {
    /** Count the list result, append '+' if there are more pages, and set into categoryCounts */
    let categoryCount = listResponse.results.length.toString();
    if (listResponse.next) {
      categoryCount = categoryCount + '+';
    }
    let newCategoryCounts = { ...this.state.categoryCounts };
    newCategoryCounts[category] = categoryCount;
    this.setState({ categoryCounts: newCategoryCounts });
  };

  render() {
    const { classes } = this.props;
    const { categoryCounts, selectedCategory } = this.state;
    return (
      <Page gutterTop defaultSearch={ searchQuery.search }>
        {
        <BodySection gutterBottom>
          <Grid container spacing={8}>
            <Grid item xs={12} sm={12} md={3} lg={3}>
              <Paper className={ classes.categorySelection } >
                <MenuList>{
                  categories.map(category => (
                    <MenuItem key={ category[0] } onClick={ this.handleSelected(category[0]) }
                              selected={ selectedCategory === category[0] } >
                      { category[0] }
                      {
                        categoryCounts[category[0]]
                        ?
                        <Chip className={ classes.resultCount }
                              label={ categoryCounts[category[0]] }
                        />
                        :
                        null
                      }
                    </MenuItem>
                  ))
                }</MenuList>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={12} md={9} lg={9}>{
              categories.map(category => {
                const FetchComponent = category[1];
                return (
                  <div key={category[0]}
                       className={selectedCategory === category[0] ? null : classes.hidden}>
                    <FetchComponent
                      query={searchQuery}
                      onFetched={this.handleFetched(category[0])}
                      componentProps={{ GridItemProps: { xs: 12, sm: 4, md: 4, lg: 3, xl: 3 } }}
                    />
                  </div>
                )
              })
            }</Grid>
          </Grid>
        </BodySection>
        }
      </Page>
    );
  }
}

const styles = theme => ({
  categorySelection: {
    height: '100%',
    // the category selection has a horizontal layout for the SM/XS displays
    [theme.breakpoints.down('sm')]: {
      '& >ul': {
        padding: 0
      },
      '& >ul>li': {
        display: 'inline-block',
        paddingBottom: 20
      },
    },
    // the horizontal category selection needs a smaller font for the XS display
    [theme.breakpoints.down('xs')]: {
      '& *': {
        fontSize: '0.9em',
      },
      '& >ul>li': {
        padding: 10,
      },
    },
  },
  hidden: {
    display: 'none'
  },
  resultCount: {
    backgroundColor: theme.palette.primary.light,
    marginLeft: 10,
    // the horizontal category selection needs a smaller chips for the XS display
    [theme.breakpoints.down('xs')]: {
      height: 25,
      width: 25,
    },
  },
});

export default withStyles(styles)(SearchPage);
