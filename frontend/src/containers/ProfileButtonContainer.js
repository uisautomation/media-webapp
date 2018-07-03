import React from 'react';

import {withProfile} from "../providers/ProfileProvider";
import ProfileButton from "../components/ProfileButton";

/**
 * A container for ``ProfileButton`` which provides it with a profile.
 */
export default withProfile(ProfileButton);
