import React from 'react';
import PropTypes from 'prop-types';

import { Link } from 'react-router-dom'

import Avatar from '@material-ui/core/Avatar';
import Collapse from '@material-ui/core/Collapse';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemAvatar from '@material-ui/core/ListItemAvatar';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import { withStyles } from '@material-ui/core/styles';

import ShowMoreIcon from '@material-ui/icons/KeyboardArrowDown';

const styles = theme => ({
  toggleButtonIcon: {
    transition: theme.transitions.create('transform'),
  },

  toggleButtonIconShowMore: {
    transform: 'rotate(0)',
  },

  toggleButtonIconHideMore: {
    transform: 'rotate(180deg)',
  },

  channelName: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
});

/**
 * A variant of the Material UI "List" component which renders a list of channels suitable for use
 * in a navigation panel.
 *
 * Unrecognised props are broadcast to the root List component.
 */
class ChannelsMuiList extends React.Component {
  state = {
    showMore: false,
  }

  render() {
    const { showMore } = this.state;
    const { classes, channels, trimCount, ...otherProps } = this.props;

    const channelItems = channels.map(channel => (
      <ListItem key={channel.id} button component={Link} to={`/channels/${channel.id}`}>
        <ListItemAvatar><Avatar>{ channel.title[0] }</Avatar></ListItemAvatar>
        <ListItemText
          primary={
            <div className={ classes.channelName }>
              { channel.title }
            </div>
          }
          secondary={
            Number(channel.mediaCount) + ' ' +
            (channel.mediaCount === 1 ? 'item' : 'items')
          }
        />
      </ListItem>
    ));

    // Split list of items into the "before" and "after" trim.
    const beforeTrim = trimCount ? channelItems.slice(0, trimCount) : channelItems;
    const afterTrim = trimCount ? channelItems.slice(trimCount) : [];

    return <List {...otherProps}>
      { beforeTrim }
      {
        afterTrim.length > 0
        ?
        <div>
          <Collapse in={ showMore }>
            { afterTrim }
          </Collapse>
          <ListItem
            button disableRipple
            onClick={() => this.setState(
              ({ showMore: prevShowMore }) => ({ showMore: !prevShowMore })
            )}
          >
            <ListItemIcon>
              <ShowMoreIcon className={
                [
                  classes.toggleButtonIcon,
                  showMore ? classes.toggleButtonIconHideMore : classes.toggleButtonIconShowMore,
                ].join(' ')
              }/>
            </ListItemIcon>
            <ListItemText primary={ showMore ? 'Show fewer' : 'Show more' } />
          </ListItem>
        </div>
        :
        null
      }
    </List>;
  }
}

ChannelsMuiList.propTypes = {
  /** Maximum number of channels to display before displaying the show more/fewer control. */
  trimCount: PropTypes.number,

  /** Array of channel resources. */
  channels: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    mediaCount: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
  })),
};

export default withStyles(styles)(ChannelsMuiList);
